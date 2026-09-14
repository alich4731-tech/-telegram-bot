create table if not exists public.ai_usage (
    telegram_user_id bigint primary key,
    question_count integer not null default 0,
    updated_at timestamptz not null default now()
);

create or replace function public.consume_ai_question(
    p_telegram_user_id bigint,
    p_limit integer
)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
    current_count integer;
begin
    insert into public.ai_usage (telegram_user_id, question_count, updated_at)
    values (p_telegram_user_id, 0, now())
    on conflict (telegram_user_id) do nothing;

    select question_count
    into current_count
    from public.ai_usage
    where telegram_user_id = p_telegram_user_id
    for update;

    if current_count >= p_limit then
        return 0;
    end if;

    current_count := current_count + 1;

    update public.ai_usage
    set question_count = current_count,
        updated_at = now()
    where telegram_user_id = p_telegram_user_id;

    return greatest(0, p_limit - current_count);
end;
$$;

alter table public.ai_usage enable row level security;

revoke all on table public.ai_usage from anon, authenticated;
revoke all on function public.consume_ai_question(bigint, integer) from public;
