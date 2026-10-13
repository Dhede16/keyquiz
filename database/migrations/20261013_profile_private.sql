BEGIN;

DO $$
DECLARE
    legacy_column_count INTEGER;
    has_legacy_columns BOOLEAN;
    has_invalid_gender BOOLEAN;
BEGIN
    SELECT COUNT(*)
    INTO legacy_column_count
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'profiles'
      AND column_name IN ('birth_date', 'phone', 'gender');

    IF legacy_column_count NOT IN (0, 3) THEN
        RAISE EXCEPTION
            'Cannot migrate profile_private: run 20261006_profile_columns.sql before this migration.';
    END IF;

    has_legacy_columns := legacy_column_count = 3;
    IF has_legacy_columns THEN
        EXECUTE $query$
            SELECT EXISTS (
                SELECT 1
                FROM public.profiles
                WHERE gender IS NOT NULL
                  AND gender NOT IN ('laki-laki', 'perempuan')
            )
        $query$ INTO has_invalid_gender;

        IF has_invalid_gender THEN
            RAISE EXCEPTION
                'Cannot migrate profile_private: normalize invalid profiles.gender values before retrying.';
        END IF;
    END IF;
END;
$$;

CREATE TABLE IF NOT EXISTS public.profile_private (
    user_id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    birth_date DATE,
    phone TEXT,
    gender TEXT CHECK (gender IN ('laki-laki', 'perempuan')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$
DECLARE
    has_legacy_columns BOOLEAN;
BEGIN
    SELECT COUNT(*) = 3
    INTO has_legacy_columns
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'profiles'
      AND column_name IN ('birth_date', 'phone', 'gender');

    IF has_legacy_columns THEN
        EXECUTE $query$
            INSERT INTO public.profile_private AS existing
                (user_id, birth_date, phone, gender)
            SELECT id, birth_date, phone, gender
            FROM public.profiles
            WHERE birth_date IS NOT NULL OR phone IS NOT NULL OR gender IS NOT NULL
            ON CONFLICT (user_id) DO UPDATE
            SET birth_date = COALESCE(existing.birth_date, EXCLUDED.birth_date),
                phone = COALESCE(existing.phone, EXCLUDED.phone),
                gender = COALESCE(existing.gender, EXCLUDED.gender)
        $query$;
    END IF;
END;
$$;

ALTER TABLE public.profiles
    DROP COLUMN IF EXISTS birth_date,
    DROP COLUMN IF EXISTS phone,
    DROP COLUMN IF EXISTS gender;

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

DROP TRIGGER IF EXISTS tr_profile_private_updated_at ON public.profile_private;
CREATE TRIGGER tr_profile_private_updated_at
BEFORE UPDATE ON public.profile_private
FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_private ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public profiles are viewable by authenticated users" ON public.profiles;
DROP POLICY IF EXISTS "Users can insert their own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can update their own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can view profiles in their class community" ON public.profiles;
CREATE POLICY "Users can view profiles in their class community"
ON public.profiles FOR SELECT TO authenticated
USING (public.can_view_profile(id));

DROP POLICY IF EXISTS "Users can view their own private profile" ON public.profile_private;
CREATE POLICY "Users can view their own private profile"
ON public.profile_private FOR SELECT TO authenticated
USING (auth.uid() = user_id);

REVOKE ALL ON TABLE public.profiles FROM anon, authenticated;
GRANT SELECT (id, email, name, role, avatar_url, created_at, updated_at)
ON TABLE public.profiles TO authenticated;

REVOKE ALL ON TABLE public.profile_private FROM anon, authenticated;
GRANT SELECT ON TABLE public.profile_private TO authenticated;

REVOKE ALL ON FUNCTION public.can_view_profile(UUID) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.can_view_profile(UUID) TO authenticated;

REVOKE ALL ON FUNCTION public.update_own_profile(TEXT, TEXT, DATE, TEXT, TEXT)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.update_own_profile(TEXT, TEXT, DATE, TEXT, TEXT)
TO authenticated;

NOTIFY pgrst, 'reload schema';
COMMIT;
