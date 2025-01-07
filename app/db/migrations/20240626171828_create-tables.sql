-- migrate:up
create table categories (
    id serial primary key,
    name varchar(50),
    currency varchar(5),
    CONSTRAINT unique_name UNIQUE (name)
);

create table balance (
    id serial primary key,
    cat_id int REFERENCES categories (id),
    date timestamp with time zone default current_timestamp,
    value int,
    rate int,
    CONSTRAINT unique_cat_date UNIQUE (cat_id, date)
);

-- migrate:down
drop table if exists balance;
drop table if exists categories;
