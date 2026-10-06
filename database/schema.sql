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
    birth_date DATE,
    phone TEXT,
    gender TEXT CHECK (gender IN ('laki-laki', 'perempuan')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS birth_date DATE;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS phone TEXT;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS gender TEXT CHECK (gender IN ('laki-laki', 'perempuan'));

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
        COALESCE(NEW.raw_user_meta_data->>'role', 'student'),
        NEW.raw_user_meta_data->>'avatar_url'
    )
    ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        name = COALESCE(EXCLUDED.name, public.profiles.name),
        role = COALESCE(EXCLUDED.role, public.profiles.role);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

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

-- Ensure column migration for existing tables
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'profiles' AND column_name = 'nim_nip') THEN
        ALTER TABLE public.profiles DROP COLUMN nim_nip CASCADE;
    END IF;
END $$;

-- ==============================================================================
-- 15. ROW LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
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

-- Allow authenticated users to view profiles
DROP POLICY IF EXISTS "Public profiles are viewable by authenticated users" ON public.profiles;
CREATE POLICY "Public profiles are viewable by authenticated users" 
ON public.profiles FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Users can insert their own profile" ON public.profiles;
CREATE POLICY "Users can insert their own profile" 
ON public.profiles FOR INSERT TO authenticated WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update their own profile" ON public.profiles;
CREATE POLICY "Users can update their own profile" 
ON public.profiles FOR UPDATE TO authenticated USING (auth.uid() = id);

-- Kelas policies
DROP POLICY IF EXISTS "Anyone authenticated can view classes" ON public.kelas;
CREATE POLICY "Anyone authenticated can view classes" 
ON public.kelas FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Teachers can insert classes" ON public.kelas;
CREATE POLICY "Teachers can insert classes" 
ON public.kelas FOR INSERT TO authenticated WITH CHECK (auth.uid() = teacher_id);

DROP POLICY IF EXISTS "Teachers can update their own classes" ON public.kelas;
CREATE POLICY "Teachers can update their own classes" 
ON public.kelas FOR UPDATE TO authenticated USING (auth.uid() = teacher_id);

DROP POLICY IF EXISTS "Teachers can delete their own classes" ON public.kelas;
CREATE POLICY "Teachers can delete their own classes" 
ON public.kelas FOR DELETE TO authenticated USING (auth.uid() = teacher_id);

-- Anggota Kelas policies
DROP POLICY IF EXISTS "Members can view class membership" ON public.anggota_kelas;
CREATE POLICY "Members can view class membership" 
ON public.anggota_kelas FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Students can join class" ON public.anggota_kelas;
CREATE POLICY "Students can join class" 
ON public.anggota_kelas FOR INSERT TO authenticated WITH CHECK (auth.uid() = student_id);

DROP POLICY IF EXISTS "Students or teachers can leave/remove from class" ON public.anggota_kelas;
CREATE POLICY "Students or teachers can leave/remove from class" 
ON public.anggota_kelas FOR DELETE TO authenticated 
USING (auth.uid() = student_id OR auth.uid() IN (SELECT teacher_id FROM public.kelas WHERE id = kelas_id));

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
CREATE POLICY "Students can view and create their submissions" 
ON public.jawaban_mahasiswa FOR ALL TO authenticated 
USING (
    auth.uid() = student_id 
    OR auth.uid() IN (
        SELECT k.teacher_id FROM public.kelas k 
        JOIN public.tugas t ON t.kelas_id = k.id 
        WHERE t.id = tugas_id
    )
);

DROP POLICY IF EXISTS "Students and teachers can access submission details" ON public.detail_jawaban;
CREATE POLICY "Students and teachers can access submission details" 
ON public.detail_jawaban FOR ALL TO authenticated 
USING (
    auth.uid() IN (SELECT student_id FROM public.jawaban_mahasiswa WHERE id = submission_id)
    OR auth.uid() IN (
        SELECT k.teacher_id FROM public.kelas k 
        JOIN public.tugas t ON t.kelas_id = k.id 
        JOIN public.jawaban_mahasiswa jm ON jm.tugas_id = t.id 
        WHERE jm.id = submission_id
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
