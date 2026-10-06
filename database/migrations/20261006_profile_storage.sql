INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'profile',
    'profile',
    TRUE,
    2097152,
    ARRAY['image/jpeg']
)
ON CONFLICT (id) DO UPDATE
SET public = EXCLUDED.public,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

DROP POLICY IF EXISTS "Users can view their own profile photos" ON storage.objects;
CREATE POLICY "Users can view their own profile photos"
ON storage.objects FOR SELECT TO authenticated
USING (
    bucket_id = 'profile'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

DROP POLICY IF EXISTS "Users can upload their own profile photos" ON storage.objects;
CREATE POLICY "Users can upload their own profile photos"
ON storage.objects FOR INSERT TO authenticated
WITH CHECK (
    bucket_id = 'profile'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

DROP POLICY IF EXISTS "Users can replace their own profile photos" ON storage.objects;
CREATE POLICY "Users can replace their own profile photos"
ON storage.objects FOR UPDATE TO authenticated
USING (
    bucket_id = 'profile'
    AND (storage.foldername(name))[1] = auth.uid()::text
)
WITH CHECK (
    bucket_id = 'profile'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

DROP POLICY IF EXISTS "Users can delete their own profile photos" ON storage.objects;
CREATE POLICY "Users can delete their own profile photos"
ON storage.objects FOR DELETE TO authenticated
USING (
    bucket_id = 'profile'
    AND (storage.foldername(name))[1] = auth.uid()::text
);
