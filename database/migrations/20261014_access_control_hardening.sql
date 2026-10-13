BEGIN;

CREATE OR REPLACE FUNCTION public.can_view_class(target_class_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.kelas k
        WHERE k.id = target_class_id
          AND (
              k.teacher_id = (SELECT auth.uid())
              OR EXISTS (
                  SELECT 1
                  FROM public.anggota_kelas ak
                  WHERE ak.kelas_id = k.id
                    AND ak.student_id = (SELECT auth.uid())
              )
          )
    );
$$;

CREATE OR REPLACE FUNCTION public.can_view_class_membership(
    target_class_id UUID,
    target_student_id UUID
)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT target_student_id = (SELECT auth.uid())
        OR EXISTS (
            SELECT 1 FROM public.kelas k
            WHERE k.id = target_class_id
              AND k.teacher_id = (SELECT auth.uid())
        )
        OR EXISTS (
            SELECT 1 FROM public.anggota_kelas viewer
            WHERE viewer.kelas_id = target_class_id
              AND viewer.student_id = (SELECT auth.uid())
        );
$$;

CREATE OR REPLACE FUNCTION public.join_class_by_code(class_code TEXT)
RETURNS TABLE (
    id UUID,
    teacher_id UUID,
    title TEXT,
    major TEXT,
    description TEXT,
    code TEXT,
    created_at TIMESTAMPTZ,
    teacher_email TEXT,
    teacher_name TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    current_user_id UUID := (SELECT auth.uid());
    target_class_id UUID;
BEGIN
    IF current_user_id IS NULL THEN
        RAISE EXCEPTION 'Authentication required' USING ERRCODE = '42501';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM public.profiles p
        WHERE p.id = current_user_id AND p.role = 'student'
    ) THEN
        RAISE EXCEPTION 'Only students can join a class' USING ERRCODE = '42501';
    END IF;

    SELECT k.id
    INTO target_class_id
    FROM public.kelas k
    WHERE k.code = upper(trim(class_code));

    IF target_class_id IS NULL THEN
        RAISE EXCEPTION 'Class not found' USING ERRCODE = 'P0002';
    END IF;

    INSERT INTO public.anggota_kelas (kelas_id, student_id)
    VALUES (target_class_id, current_user_id)
    ON CONFLICT (kelas_id, student_id) DO NOTHING;

    RETURN QUERY
    SELECT k.id, k.teacher_id, k.title, k.major, k.description, k.code,
           k.created_at, p.email, p.name
    FROM public.kelas k
    JOIN public.profiles p ON p.id = k.teacher_id
    WHERE k.id = target_class_id;
END;
$$;

CREATE OR REPLACE FUNCTION public.submit_task_answers(
    target_task_id UUID,
    submitted_answers JSONB
)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    current_user_id UUID := (SELECT auth.uid());
    new_submission_id UUID;
BEGIN
    IF current_user_id IS NULL THEN
        RAISE EXCEPTION 'Authentication required' USING ERRCODE = '42501';
    END IF;

    IF submitted_answers IS NULL OR jsonb_typeof(submitted_answers) <> 'array' THEN
        RAISE EXCEPTION 'Submitted answers must be an array' USING ERRCODE = '22023';
    END IF;

    IF jsonb_array_length(submitted_answers) = 0 THEN
        RAISE EXCEPTION 'At least one answer is required' USING ERRCODE = '22023';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM public.profiles p
        WHERE p.id = current_user_id AND p.role = 'student'
    ) OR NOT EXISTS (
        SELECT 1
        FROM public.tugas t
        JOIN public.kelas k ON k.id = t.kelas_id
        JOIN public.anggota_kelas ak ON ak.kelas_id = k.id
        WHERE t.id = target_task_id
          AND ak.student_id = current_user_id
    ) THEN
        RAISE EXCEPTION 'Student is not a member of this task class' USING ERRCODE = '42501';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM jsonb_to_recordset(submitted_answers) AS a(question_id UUID, answer_text TEXT)
        LEFT JOIN public.soal s
          ON s.id = a.question_id AND s.tugas_id = target_task_id
        WHERE s.id IS NULL OR a.answer_text IS NULL
    ) OR (
        SELECT count(*) <> count(DISTINCT a.question_id)
        FROM jsonb_to_recordset(submitted_answers) AS a(question_id UUID, answer_text TEXT)
    ) THEN
        RAISE EXCEPTION 'Submitted answers do not match task questions' USING ERRCODE = '22023';
    END IF;

    INSERT INTO public.jawaban_mahasiswa (tugas_id, student_id, status, is_scanned)
    VALUES (target_task_id, current_user_id, 'submitted', FALSE)
    RETURNING id INTO new_submission_id;

    INSERT INTO public.detail_jawaban (submission_id, soal_id, jawaban_teks)
    SELECT new_submission_id, a.question_id, a.answer_text
    FROM jsonb_to_recordset(submitted_answers) AS a(question_id UUID, answer_text TEXT);

    RETURN new_submission_id;
END;
$$;

CREATE OR REPLACE FUNCTION public.get_class_answer_keys(target_class_id UUID)
RETURNS TABLE (
    task_id UUID,
    soal_id UUID,
    opsi_jawaban_id UUID,
    option_letter TEXT,
    option_text TEXT,
    is_correct BOOLEAN,
    answer_key TEXT,
    rubric JSONB
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT t.id, s.id, o.id, o.option_letter, o.option_text, o.is_correct,
           e.answer_key, e.rubric
    FROM public.kelas k
    JOIN public.tugas t ON t.kelas_id = k.id
    JOIN public.soal s ON s.tugas_id = t.id
    LEFT JOIN public.opsi_jawaban o ON o.soal_id = s.id
    LEFT JOIN public.kunci_jawaban_essay e ON e.soal_id = s.id
    WHERE k.id = target_class_id
      AND (
          k.teacher_id = (SELECT auth.uid())
          OR (
              EXISTS (
                  SELECT 1
                  FROM public.anggota_kelas ak
                  WHERE ak.kelas_id = k.id
                    AND ak.student_id = (SELECT auth.uid())
              )
              AND t.show_correct_answers
              AND EXISTS (
                  SELECT 1
                  FROM public.jawaban_mahasiswa jm
                  WHERE jm.tugas_id = t.id
                    AND jm.student_id = (SELECT auth.uid())
                    AND jm.status = 'graded'
              )
          )
      );
$$;

CREATE OR REPLACE FUNCTION public.grade_submission(
    target_submission_id UUID,
    final_total NUMERIC,
    question_scores JSONB DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    current_user_id UUID := (SELECT auth.uid());
    target_task_id UUID;
    maximum_total NUMERIC;
    expected_question_count INTEGER;
    updated_question_count INTEGER := 0;
    calculated_total NUMERIC := 0;
    score_entry RECORD;
    score_value NUMERIC;
BEGIN
    IF current_user_id IS NULL THEN
        RAISE EXCEPTION 'Authentication required' USING ERRCODE = '42501';
    END IF;

    SELECT t.id
    INTO target_task_id
    FROM public.jawaban_mahasiswa jm
    JOIN public.tugas t ON t.id = jm.tugas_id
    JOIN public.kelas k ON k.id = t.kelas_id
    WHERE jm.id = target_submission_id
      AND k.teacher_id = current_user_id
    FOR UPDATE OF jm;

    IF target_task_id IS NULL THEN
        RAISE EXCEPTION 'Submission not found for this teacher' USING ERRCODE = '42501';
    END IF;

    IF final_total IS NULL OR final_total < 0 THEN
        RAISE EXCEPTION 'Final score must be zero or greater' USING ERRCODE = '22023';
    END IF;

    SELECT COALESCE(sum(COALESCE(s.points, 10)), 0)
    INTO maximum_total
    FROM public.soal s
    WHERE s.tugas_id = target_task_id;

    IF final_total > maximum_total THEN
        RAISE EXCEPTION 'Final score exceeds the task maximum' USING ERRCODE = '22023';
    END IF;

    IF question_scores IS NOT NULL THEN
        IF jsonb_typeof(question_scores) <> 'object' THEN
            RAISE EXCEPTION 'Question scores must be an object' USING ERRCODE = '22023';
        END IF;

        SELECT count(*)
        INTO expected_question_count
        FROM public.soal s
        WHERE s.tugas_id = target_task_id;

        FOR score_entry IN
            SELECT key, value FROM jsonb_each(question_scores)
        LOOP
            IF jsonb_typeof(score_entry.value) <> 'number' THEN
                RAISE EXCEPTION 'Question scores must be numeric' USING ERRCODE = '22023';
            END IF;
            score_value := (score_entry.value::TEXT)::NUMERIC;

            UPDATE public.detail_jawaban dj
            SET nilai_final = score_value
            FROM public.soal s
            WHERE dj.submission_id = target_submission_id
              AND dj.soal_id = s.id
              AND s.tugas_id = target_task_id
              AND s.id = score_entry.key::UUID
              AND score_value BETWEEN 0 AND COALESCE(s.points, 10);

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Score is invalid or answer is missing' USING ERRCODE = '22023';
            END IF;

            updated_question_count := updated_question_count + 1;
            calculated_total := calculated_total + score_value;
        END LOOP;

        IF updated_question_count <> expected_question_count
           OR abs(calculated_total - final_total) > 0.01 THEN
            RAISE EXCEPTION 'Question scores must cover the task and match the final score' USING ERRCODE = '22023';
        END IF;
    END IF;

    UPDATE public.jawaban_mahasiswa
    SET total_score = final_total,
        status = 'graded',
        graded_at = NOW()
    WHERE id = target_submission_id;
END;
$$;

REVOKE ALL ON FUNCTION public.join_class_by_code(TEXT) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.join_class_by_code(TEXT) TO authenticated;
REVOKE ALL ON FUNCTION public.submit_task_answers(UUID, JSONB) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.submit_task_answers(UUID, JSONB) TO authenticated;
REVOKE ALL ON FUNCTION public.get_class_answer_keys(UUID) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.get_class_answer_keys(UUID) TO authenticated;
REVOKE ALL ON FUNCTION public.grade_submission(UUID, NUMERIC, JSONB) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.grade_submission(UUID, NUMERIC, JSONB) TO authenticated;
REVOKE ALL ON FUNCTION public.can_view_class(UUID) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.can_view_class(UUID) TO authenticated;
REVOKE ALL ON FUNCTION public.can_view_class_membership(UUID, UUID) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.can_view_class_membership(UUID, UUID) TO authenticated;

DROP POLICY IF EXISTS "Anyone authenticated can view classes" ON public.kelas;
DROP POLICY IF EXISTS "Teachers can view their classes and members can view joined classes" ON public.kelas;
CREATE POLICY "Teachers can view their classes and members can view joined classes"
ON public.kelas FOR SELECT TO authenticated
USING (
    public.can_view_class(id)
);

DROP POLICY IF EXISTS "Teachers can insert classes" ON public.kelas;
CREATE POLICY "Teachers can insert classes"
ON public.kelas FOR INSERT TO authenticated
WITH CHECK (
    teacher_id = (SELECT auth.uid())
    AND EXISTS (
        SELECT 1 FROM public.profiles p
        WHERE p.id = (SELECT auth.uid()) AND p.role = 'teacher'
    )
);

DROP POLICY IF EXISTS "Teachers can update their own classes" ON public.kelas;
CREATE POLICY "Teachers can update their own classes"
ON public.kelas FOR UPDATE TO authenticated
USING (teacher_id = (SELECT auth.uid()))
WITH CHECK (teacher_id = (SELECT auth.uid()));

DROP POLICY IF EXISTS "Teachers can delete their own classes" ON public.kelas;
CREATE POLICY "Teachers can delete their own classes"
ON public.kelas FOR DELETE TO authenticated
USING (teacher_id = (SELECT auth.uid()));

DROP POLICY IF EXISTS "Members can view class membership" ON public.anggota_kelas;
CREATE POLICY "Members can view class membership"
ON public.anggota_kelas FOR SELECT TO authenticated
USING (
    public.can_view_class_membership(kelas_id, student_id)
);

DROP POLICY IF EXISTS "Students can join class" ON public.anggota_kelas;
REVOKE INSERT ON TABLE public.anggota_kelas FROM anon, authenticated;
DROP POLICY IF EXISTS "Students or teachers can leave/remove from class" ON public.anggota_kelas;
CREATE POLICY "Students or teachers can leave/remove from class"
ON public.anggota_kelas FOR DELETE TO authenticated
USING (
    student_id = (SELECT auth.uid())
    OR EXISTS (
        SELECT 1 FROM public.kelas k
        WHERE k.id = kelas_id AND k.teacher_id = (SELECT auth.uid())
    )
);

DROP POLICY IF EXISTS "Students can view and create their submissions" ON public.jawaban_mahasiswa;
DROP POLICY IF EXISTS "Students can view their own submissions" ON public.jawaban_mahasiswa;
CREATE POLICY "Students can view their own submissions"
ON public.jawaban_mahasiswa FOR SELECT TO authenticated
USING (
    student_id = (SELECT auth.uid())
    OR EXISTS (
        SELECT 1
        FROM public.tugas t
        JOIN public.kelas k ON k.id = t.kelas_id
        WHERE t.id = tugas_id AND k.teacher_id = (SELECT auth.uid())
    )
);

DROP POLICY IF EXISTS "Students can submit their own ungraded work" ON public.jawaban_mahasiswa;
CREATE POLICY "Students can submit their own ungraded work"
ON public.jawaban_mahasiswa FOR INSERT TO authenticated
WITH CHECK (
    student_id = (SELECT auth.uid())
    AND status = 'submitted'
    AND total_score IS NULL
    AND is_scanned = FALSE
    AND file_scan_url IS NULL
    AND graded_at IS NULL
    AND EXISTS (
        SELECT 1
        FROM public.tugas t
        JOIN public.kelas k ON k.id = t.kelas_id
        JOIN public.anggota_kelas ak ON ak.kelas_id = k.id
        WHERE t.id = tugas_id
          AND ak.student_id = (SELECT auth.uid())
    )
);

DROP POLICY IF EXISTS "Teachers can manage their class submissions" ON public.jawaban_mahasiswa;
CREATE POLICY "Teachers can manage their class submissions"
ON public.jawaban_mahasiswa FOR ALL TO authenticated
USING (
    EXISTS (
        SELECT 1
        FROM public.tugas t
        JOIN public.kelas k ON k.id = t.kelas_id
        WHERE t.id = tugas_id AND k.teacher_id = (SELECT auth.uid())
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM public.tugas t
        JOIN public.kelas k ON k.id = t.kelas_id
        WHERE t.id = tugas_id AND k.teacher_id = (SELECT auth.uid())
    )
);

DROP POLICY IF EXISTS "Students and teachers can access submission details" ON public.detail_jawaban;
DROP POLICY IF EXISTS "Students can view their own answer details" ON public.detail_jawaban;
CREATE POLICY "Students can view their own answer details"
ON public.detail_jawaban FOR SELECT TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.jawaban_mahasiswa jm
        WHERE jm.id = submission_id AND jm.student_id = (SELECT auth.uid())
    )
    OR EXISTS (
        SELECT 1
        FROM public.jawaban_mahasiswa jm
        JOIN public.tugas t ON t.id = jm.tugas_id
        JOIN public.kelas k ON k.id = t.kelas_id
        WHERE jm.id = submission_id AND k.teacher_id = (SELECT auth.uid())
    )
);

DROP POLICY IF EXISTS "Students can submit answer text only" ON public.detail_jawaban;
CREATE POLICY "Students can submit answer text only"
ON public.detail_jawaban FOR INSERT TO authenticated
WITH CHECK (
    similarity_score IS NULL
    AND rubric_evaluation IS NULL
    AND nilai_ai IS NULL
    AND nilai_final IS NULL
    AND teacher_feedback IS NULL
    AND is_revised_by_teacher = FALSE
    AND EXISTS (
        SELECT 1
        FROM public.jawaban_mahasiswa jm
        JOIN public.tugas t ON t.id = jm.tugas_id
        JOIN public.kelas k ON k.id = t.kelas_id
        JOIN public.anggota_kelas ak ON ak.kelas_id = k.id
        JOIN public.soal s ON s.id = soal_id AND s.tugas_id = t.id
        WHERE jm.id = submission_id
          AND jm.student_id = (SELECT auth.uid())
          AND jm.status = 'submitted'
          AND jm.is_scanned = FALSE
          AND ak.student_id = (SELECT auth.uid())
          AND (
              opsi_jawaban_id IS NULL
              OR EXISTS (
                  SELECT 1 FROM public.opsi_jawaban o
                  WHERE o.id = opsi_jawaban_id AND o.soal_id = s.id
              )
          )
    )
);

DROP POLICY IF EXISTS "Teachers can manage their class answer details" ON public.detail_jawaban;
CREATE POLICY "Teachers can manage their class answer details"
ON public.detail_jawaban FOR ALL TO authenticated
USING (
    EXISTS (
        SELECT 1
        FROM public.jawaban_mahasiswa jm
        JOIN public.tugas t ON t.id = jm.tugas_id
        JOIN public.kelas k ON k.id = t.kelas_id
        WHERE jm.id = submission_id AND k.teacher_id = (SELECT auth.uid())
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM public.jawaban_mahasiswa jm
        JOIN public.tugas t ON t.id = jm.tugas_id
        JOIN public.kelas k ON k.id = t.kelas_id
        JOIN public.soal s ON s.id = soal_id AND s.tugas_id = t.id
        WHERE jm.id = submission_id AND k.teacher_id = (SELECT auth.uid())
    )
);

REVOKE SELECT ON TABLE public.opsi_jawaban FROM anon, authenticated;
GRANT SELECT (id, soal_id, option_letter, option_text, order_index)
ON TABLE public.opsi_jawaban TO authenticated;
GRANT INSERT, UPDATE, DELETE ON TABLE public.opsi_jawaban TO authenticated;

NOTIFY pgrst, 'reload schema';
COMMIT;
