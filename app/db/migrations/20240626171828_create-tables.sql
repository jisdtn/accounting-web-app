-- migrate:up
create table categories (
    id serial primary key,
    name varchar(50),
    currency varchar(5)
);

create table balance (
    id serial primary key,
    cat_id int REFERENCES categories (id),
    date timestamp with time zone default current_timestamp,
    value int,
    rate int
);

-- migrate:down
