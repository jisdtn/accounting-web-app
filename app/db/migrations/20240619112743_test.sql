-- migrate:up
create table test (
  test_text varchar(255),
  created_at timestamp default current_timestamp
);

-- migrate:down
