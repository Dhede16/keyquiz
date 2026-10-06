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

ALTER TABLE public.scan_archive_folders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scan_archives ENABLE ROW LEVEL SECURITY;

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

NOTIFY pgrst, 'reload schema';
