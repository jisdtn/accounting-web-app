-- migrate:up
create table test (
  test_text varchar(255),
  created_at timestamp with time zone default current_timestamp
);

-- migrate:down
