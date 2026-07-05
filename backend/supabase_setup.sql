-- Run this SQL in your Supabase dashboard:
-- Go to https://supabase.com → Your Project → SQL Editor → New Query → Paste this → Run

CREATE TABLE IF NOT EXISTS public.user_preferences (
    id            BIGSERIAL PRIMARY KEY,
    user_id       TEXT        NOT NULL,
    errand_type   TEXT        NOT NULL,
    preferred_location TEXT   NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, errand_type)
);

-- Enable Row Level Security (good practice)
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;

-- Allow service role full access (our backend uses the secret key)
CREATE POLICY "service_role_all" ON public.user_preferences
    FOR ALL
    USING (true)
    WITH CHECK (true);
