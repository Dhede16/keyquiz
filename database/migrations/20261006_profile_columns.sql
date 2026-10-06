ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS birth_date DATE,
    ADD COLUMN IF NOT EXISTS phone TEXT,
    ADD COLUMN IF NOT EXISTS gender TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.profiles'::regclass
          AND conname = 'profiles_gender_check'
    ) THEN
        ALTER TABLE public.profiles
            ADD CONSTRAINT profiles_gender_check
            CHECK (gender IN ('laki-laki', 'perempuan')) NOT VALID;
    END IF;
END
$$;

NOTIFY pgrst, 'reload schema';
