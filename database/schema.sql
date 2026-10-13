-- ==============================================================================
-- KEYQUIZ - SUPABASE DATABASE SCHEMA DDL
-- ==============================================================================

-- 1. Enable UUID Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. ENUM TYPES & FUNCTIONS
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ==============================================================================
-- 3. TABEL PROFILES (Ekstensi dari Supabase auth.users)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('teacher', 'student')) DEFAULT 'student',
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.profile_private (
    user_id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    birth_date DATE,
    phone TEXT,
    gender TEXT CHECK (gender IN ('laki-laki', 'perempuan')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.keyquiz_schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- 4. TABEL KELAS
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.kelas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    major TEXT,
    description TEXT,
    code TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- 5. TABEL ANGGOTA_KELAS (Relasi Mahasiswa yang bergabung ke Kelas)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.anggota_kelas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kelas_id UUID NOT NULL REFERENCES public.kelas(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_kelas_student UNIQUE (kelas_id, student_id)
);

-- ==============================================================================
-- 6. TABEL TUGAS
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.tugas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kelas_id UUID NOT NULL REFERENCES public.kelas(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    deadline TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (status IN ('draft', 'published', 'closed')) DEFAULT 'published',
    show_score BOOLEAN DEFAULT TRUE,
    show_correct_answers BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- 7. TABEL SOAL (Multiple Choice & Essay)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.soal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tugas_id UUID NOT NULL REFERENCES public.tugas(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('multiple_choice', 'essay', 'short_answer')),
    question_text TEXT NOT NULL,
    points NUMERIC DEFAULT 10,
    order_index INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- 8. TABEL OPSI_JAWABAN (Pilihan Ganda A/B/C/D/E)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.opsi_jawaban (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    soal_id UUID NOT NULL REFERENCES public.soal(id) ON DELETE CASCADE,
    option_letter TEXT NOT NULL, -- 'A', 'B', 'C', 'D', 'E'
    option_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    order_index INTEGER DEFAULT 1
);

-- ==============================================================================
-- 9. TABEL KUNCI_JAWABAN_ESSAY (Acuan ChromaDB & Rubrik LLM)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.kunci_jawaban_essay (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- ID ini sama dengan ID Document di ChromaDB
    soal_id UUID UNIQUE NOT NULL REFERENCES public.soal(id) ON DELETE CASCADE,
    answer_key TEXT NOT NULL,
    rubric JSONB DEFAULT '[]'::jsonb, -- Array string kriteria rubrik
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- 10. TABEL JAWABAN_MAHASISWA (Header Pengumpulan Tugas)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.jawaban_mahasiswa (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tugas_id UUID NOT NULL REFERENCES public.tugas(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('submitted', 'graded', 'draft')) DEFAULT 'submitted',
    total_score NUMERIC DEFAULT NULL,
    is_scanned BOOLEAN DEFAULT FALSE,
    file_scan_url TEXT DEFAULT NULL,
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    graded_at TIMESTAMPTZ DEFAULT NULL,
    CONSTRAINT unique_tugas_student UNIQUE (tugas_id, student_id)
);

-- ==============================================================================
-- 11. TABEL DETAIL_JAWABAN (Jawaban per Nomor Soal & Skor AI vs Final)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.detail_jawaban (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- ID ini sama dengan ID Document Jawaban di ChromaDB
    submission_id UUID NOT NULL REFERENCES public.jawaban_mahasiswa(id) ON DELETE CASCADE,
    soal_id UUID NOT NULL REFERENCES public.soal(id) ON DELETE CASCADE,
    opsi_jawaban_id UUID REFERENCES public.opsi_jawaban(id) ON DELETE SET NULL,
    jawaban_teks TEXT DEFAULT NULL,
    similarity_score NUMERIC DEFAULT NULL,
    rubric_evaluation JSONB DEFAULT NULL,
    nilai_ai NUMERIC DEFAULT NULL,
    nilai_final NUMERIC DEFAULT NULL,
    is_revised_by_teacher BOOLEAN DEFAULT FALSE,
    teacher_feedback TEXT DEFAULT NULL,
    yakin_scan BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- 12. FOLDER ARSIP HASIL SCAN
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.scan_archive_folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL REFERENCES public.kelas(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK (char_length(trim(name)) BETWEEN 1 AND 100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (id, class_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS scan_archive_folders_class_name_unique
ON public.scan_archive_folders (class_id, lower(name));

CREATE TABLE IF NOT EXISTS public.scan_archives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL REFERENCES public.kelas(id) ON DELETE CASCADE,
    folder_id UUID NOT NULL,
    task_id UUID NOT NULL UNIQUE REFERENCES public.tugas(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    quiz_title TEXT NOT NULL,
    original_file_path TEXT NOT NULL UNIQUE,
    questions JSONB NOT NULL CHECK (jsonb_typeof(questions) = 'array'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (folder_id, class_id)
        REFERENCES public.scan_archive_folders(id, class_id)
        ON DELETE CASCADE
);

-- Index foreign-key columns used by class, task, submission, and RLS lookups.
CREATE INDEX IF NOT EXISTS idx_kelas_teacher_id ON public.kelas (teacher_id);
CREATE INDEX IF NOT EXISTS idx_anggota_kelas_student_id ON public.anggota_kelas (student_id);
CREATE INDEX IF NOT EXISTS idx_tugas_kelas_id ON public.tugas (kelas_id);
CREATE INDEX IF NOT EXISTS idx_soal_tugas_id ON public.soal (tugas_id);
CREATE INDEX IF NOT EXISTS idx_opsi_jawaban_soal_id ON public.opsi_jawaban (soal_id);
CREATE INDEX IF NOT EXISTS idx_jawaban_mahasiswa_student_id ON public.jawaban_mahasiswa (student_id);
CREATE INDEX IF NOT EXISTS idx_detail_jawaban_submission_id ON public.detail_jawaban (submission_id);
CREATE INDEX IF NOT EXISTS idx_detail_jawaban_soal_id ON public.detail_jawaban (soal_id);
CREATE INDEX IF NOT EXISTS idx_detail_jawaban_opsi_jawaban_id ON public.detail_jawaban (opsi_jawaban_id);
CREATE INDEX IF NOT EXISTS idx_scan_archive_folders_created_by ON public.scan_archive_folders (created_by);
CREATE INDEX IF NOT EXISTS idx_scan_archives_class_id ON public.scan_archives (class_id);
CREATE INDEX IF NOT EXISTS idx_scan_archives_folder_id_class_id ON public.scan_archives (folder_id, class_id);
CREATE INDEX IF NOT EXISTS idx_scan_archives_student_id ON public.scan_archives (student_id);

-- ==============================================================================
-- 13. AUTOMATIC PROFILE CREATION TRIGGER (Dari Supabase Auth)
-- ==============================================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, name, role, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
        'student',
        NEW.raw_user_meta_data->>'avatar_url'
    )
    ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        name = COALESCE(EXCLUDED.name, public.profiles.name),
        avatar_url = COALESCE(EXCLUDED.avatar_url, public.profiles.avatar_url);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = '';

CREATE OR REPLACE FUNCTION public.can_view_profile(target_profile_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT target_profile_id = (SELECT auth.uid())
        OR EXISTS (
            SELECT 1
            FROM public.kelas k
            JOIN public.anggota_kelas ak ON ak.kelas_id = k.id
            WHERE k.teacher_id = (SELECT auth.uid())
              AND ak.student_id = target_profile_id
        )
        OR EXISTS (
            SELECT 1
            FROM public.anggota_kelas viewer
            JOIN public.anggota_kelas subject USING (kelas_id)
            WHERE viewer.student_id = (SELECT auth.uid())
              AND subject.student_id = target_profile_id
        )
        OR EXISTS (
            SELECT 1
            FROM public.kelas k
            JOIN public.anggota_kelas ak ON ak.kelas_id = k.id
            WHERE ak.student_id = (SELECT auth.uid())
              AND k.teacher_id = target_profile_id
        );
$$;

CREATE OR REPLACE FUNCTION public.update_own_profile(
    profile_name TEXT,
    profile_avatar_url TEXT,
    private_birth_date DATE,
    private_phone TEXT,
    private_gender TEXT
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    current_user_id UUID := (SELECT auth.uid());
BEGIN
    IF current_user_id IS NULL THEN
        RAISE EXCEPTION 'Authentication required' USING ERRCODE = '42501';
    END IF;

    UPDATE public.profiles
    SET name = profile_name,
        avatar_url = profile_avatar_url
    WHERE id = current_user_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Profile not found' USING ERRCODE = 'P0002';
    END IF;

    INSERT INTO public.profile_private (user_id, birth_date, phone, gender)
    VALUES (current_user_id, private_birth_date, private_phone, private_gender)
    ON CONFLICT (user_id) DO UPDATE
    SET birth_date = EXCLUDED.birth_date,
        phone = EXCLUDED.phone,
        gender = EXCLUDED.gender;
END;
$$;

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

-- Drop trigger if exists and recreate
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ==============================================================================
-- 14. UPDATED_AT TRIGGERS
-- ==============================================================================
DROP TRIGGER IF EXISTS tr_profiles_updated_at ON public.profiles;
CREATE TRIGGER tr_profiles_updated_at BEFORE UPDATE ON public.profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS tr_kelas_updated_at ON public.kelas;
CREATE TRIGGER tr_kelas_updated_at BEFORE UPDATE ON public.kelas FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS tr_tugas_updated_at ON public.tugas;
CREATE TRIGGER tr_tugas_updated_at BEFORE UPDATE ON public.tugas FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS tr_profile_private_updated_at ON public.profile_private;
CREATE TRIGGER tr_profile_private_updated_at BEFORE UPDATE ON public.profile_private FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==============================================================================
-- 15. ROW LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_private ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.kelas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.anggota_kelas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tugas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.soal ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.opsi_jawaban ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.kunci_jawaban_essay ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jawaban_mahasiswa ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.detail_jawaban ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scan_archive_folders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scan_archives ENABLE ROW LEVEL SECURITY;

-- Profile data is visible only to the user and their class community.
DROP POLICY IF EXISTS "Public profiles are viewable by authenticated users" ON public.profiles;
CREATE POLICY "Users can view profiles in their class community"
ON public.profiles FOR SELECT TO authenticated USING (public.can_view_profile(id));

DROP POLICY IF EXISTS "Users can insert their own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can update their own profile" ON public.profiles;

DROP POLICY IF EXISTS "Users can view their own private profile" ON public.profile_private;
CREATE POLICY "Users can view their own private profile"
ON public.profile_private FOR SELECT TO authenticated USING (auth.uid() = user_id);

-- Kelas policies
DROP POLICY IF EXISTS "Anyone authenticated can view classes" ON public.kelas;
DROP POLICY IF EXISTS "Teachers can view their classes and members can view joined classes" ON public.kelas;
CREATE POLICY "Teachers can view their classes and members can view joined classes"
ON public.kelas FOR SELECT TO authenticated USING (public.can_view_class(id));

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
ON public.kelas FOR DELETE TO authenticated USING (teacher_id = (SELECT auth.uid()));

-- Anggota Kelas policies
DROP POLICY IF EXISTS "Members can view class membership" ON public.anggota_kelas;
CREATE POLICY "Members can view class membership"
ON public.anggota_kelas FOR SELECT TO authenticated
USING (public.can_view_class_membership(kelas_id, student_id));

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

-- Tugas policies
CREATE OR REPLACE FUNCTION public.can_view_task(target_task_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.tugas t
        JOIN public.kelas k ON k.id = t.kelas_id
        WHERE t.id = target_task_id
          AND (
              k.teacher_id = auth.uid()
              OR (
                  EXISTS (
                      SELECT 1
                      FROM public.anggota_kelas ak
                      WHERE ak.kelas_id = k.id
                        AND ak.student_id = auth.uid()
                  )
                  AND (
                      NOT EXISTS (
                          SELECT 1
                          FROM public.jawaban_mahasiswa scan
                          WHERE scan.tugas_id = t.id
                            AND scan.is_scanned = TRUE
                      )
                      OR EXISTS (
                          SELECT 1
                          FROM public.jawaban_mahasiswa scan
                          WHERE scan.tugas_id = t.id
                            AND scan.is_scanned = TRUE
                            AND scan.student_id = auth.uid()
                      )
                  )
              )
          )
    );
$$;

REVOKE ALL ON FUNCTION public.can_view_task(UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.can_view_task(UUID) TO authenticated;

DROP POLICY IF EXISTS "Class members and teachers can view tasks" ON public.tugas;
CREATE POLICY "Class members and teachers can view tasks" 
ON public.tugas FOR SELECT TO authenticated USING (public.can_view_task(id));

DROP POLICY IF EXISTS "Teachers can manage tasks" ON public.tugas;
CREATE POLICY "Teachers can manage tasks" 
ON public.tugas FOR ALL TO authenticated 
USING (auth.uid() IN (SELECT teacher_id FROM public.kelas WHERE id = kelas_id));

-- Soal & Opsi & Kunci policies
DROP POLICY IF EXISTS "Anyone in class can view questions" ON public.soal;
CREATE POLICY "Anyone in class can view questions" 
ON public.soal FOR SELECT TO authenticated USING (public.can_view_task(tugas_id));

DROP POLICY IF EXISTS "Teachers can manage questions" ON public.soal;
CREATE POLICY "Teachers can manage questions" 
ON public.soal FOR ALL TO authenticated 
USING (auth.uid() IN (
    SELECT k.teacher_id FROM public.kelas k 
    JOIN public.tugas t ON t.kelas_id = k.id 
    WHERE t.id = tugas_id
));

DROP POLICY IF EXISTS "Anyone in class can view options" ON public.opsi_jawaban;
CREATE POLICY "Anyone in class can view options" 
ON public.opsi_jawaban FOR SELECT TO authenticated USING (
    EXISTS (
        SELECT 1
        FROM public.soal s
        WHERE s.id = soal_id
          AND public.can_view_task(s.tugas_id)
    )
);

DROP POLICY IF EXISTS "Teachers can manage options" ON public.opsi_jawaban;
CREATE POLICY "Teachers can manage options" 
ON public.opsi_jawaban FOR ALL TO authenticated 
USING (auth.uid() IN (
    SELECT k.teacher_id FROM public.kelas k 
    JOIN public.tugas t ON t.kelas_id = k.id 
    JOIN public.soal s ON s.tugas_id = t.id 
    WHERE s.id = soal_id
));

DROP POLICY IF EXISTS "Teachers can manage essay keys" ON public.kunci_jawaban_essay;
CREATE POLICY "Teachers can manage essay keys" 
ON public.kunci_jawaban_essay FOR ALL TO authenticated 
USING (auth.uid() IN (
    SELECT k.teacher_id FROM public.kelas k 
    JOIN public.tugas t ON t.kelas_id = k.id 
    JOIN public.soal s ON s.tugas_id = t.id 
    WHERE s.id = soal_id
));

-- Submissions policies
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
        WHERE t.id = tugas_id AND ak.student_id = (SELECT auth.uid())
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

DROP POLICY IF EXISTS "Teachers can manage their class scan archive folders"
ON public.scan_archive_folders;
CREATE POLICY "Teachers can manage their class scan archive folders"
ON public.scan_archive_folders FOR ALL TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.kelas k
        WHERE k.id = class_id AND k.teacher_id = auth.uid()
    )
)
WITH CHECK (
    created_by = auth.uid()
    AND EXISTS (
        SELECT 1 FROM public.kelas k
        WHERE k.id = class_id AND k.teacher_id = auth.uid()
    )
);

DROP POLICY IF EXISTS "Teachers can manage their class scan archives"
ON public.scan_archives;
CREATE POLICY "Teachers can manage their class scan archives"
ON public.scan_archives FOR ALL TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.kelas k
        WHERE k.id = class_id AND k.teacher_id = auth.uid()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.kelas k
        WHERE k.id = class_id AND k.teacher_id = auth.uid()
    )
);

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'scan-archives',
    'scan-archives',
    FALSE,
    10485760,
    ARRAY['image/jpeg', 'image/png', 'image/webp']
)
ON CONFLICT (id) DO UPDATE
SET public = FALSE,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

DROP POLICY IF EXISTS "Teachers can view their class scan archive images" ON storage.objects;
CREATE POLICY "Teachers can view their class scan archive images"
ON storage.objects FOR SELECT TO authenticated
USING (
    bucket_id = 'scan-archives'
    AND EXISTS (
        SELECT 1 FROM public.kelas k
        WHERE k.id::text = (storage.foldername(name))[1]
          AND k.teacher_id = auth.uid()
    )
);

DROP POLICY IF EXISTS "Teachers can upload their class scan archive images" ON storage.objects;
CREATE POLICY "Teachers can upload their class scan archive images"
ON storage.objects FOR INSERT TO authenticated
WITH CHECK (
    bucket_id = 'scan-archives'
    AND EXISTS (
        SELECT 1 FROM public.kelas k
        WHERE k.id::text = (storage.foldername(name))[1]
          AND k.teacher_id = auth.uid()
    )
);

DROP POLICY IF EXISTS "Teachers can delete their class scan archive images" ON storage.objects;
CREATE POLICY "Teachers can delete their class scan archive images"
ON storage.objects FOR DELETE TO authenticated
USING (
    bucket_id = 'scan-archives'
    AND EXISTS (
        SELECT 1 FROM public.kelas k
        WHERE k.id::text = (storage.foldername(name))[1]
          AND k.teacher_id = auth.uid()
    )
);

REVOKE ALL ON TABLE public.profiles FROM anon, authenticated;
GRANT SELECT (id, email, name, role, avatar_url, created_at, updated_at)
ON TABLE public.profiles TO authenticated;

REVOKE ALL ON TABLE public.profile_private FROM anon, authenticated;
GRANT SELECT ON TABLE public.profile_private TO authenticated;

REVOKE SELECT ON TABLE public.opsi_jawaban FROM anon, authenticated;
GRANT SELECT (id, soal_id, option_letter, option_text, order_index)
ON TABLE public.opsi_jawaban TO authenticated;
GRANT INSERT, UPDATE, DELETE ON TABLE public.opsi_jawaban TO authenticated;

REVOKE ALL ON TABLE public.keyquiz_schema_migrations FROM anon, authenticated;

REVOKE ALL ON FUNCTION public.can_view_profile(UUID) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.can_view_profile(UUID) TO authenticated;

REVOKE ALL ON FUNCTION public.update_own_profile(TEXT, TEXT, DATE, TEXT, TEXT)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.update_own_profile(TEXT, TEXT, DATE, TEXT, TEXT)
TO authenticated;
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
