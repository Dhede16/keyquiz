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
ON public.tugas FOR SELECT TO authenticated
USING (public.can_view_task(id));

DROP POLICY IF EXISTS "Anyone in class can view questions" ON public.soal;
CREATE POLICY "Anyone in class can view questions"
ON public.soal FOR SELECT TO authenticated
USING (public.can_view_task(tugas_id));

DROP POLICY IF EXISTS "Anyone in class can view options" ON public.opsi_jawaban;
CREATE POLICY "Anyone in class can view options"
ON public.opsi_jawaban FOR SELECT TO authenticated
USING (
    EXISTS (
        SELECT 1
        FROM public.soal s
        WHERE s.id = soal_id
          AND public.can_view_task(s.tugas_id)
    )
);
