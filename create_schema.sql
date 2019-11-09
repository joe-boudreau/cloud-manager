CREATE DATABASE a2;
USE a2;

-- DROP TABLE config;

CREATE TABLE config (
    id int not null auto_increment UNIQUE,
    upper_threshold float not null,
    lower_threshold float not null,
    shrink_ratio float not null,
    expand_ratio float not null,
    primary key (id)
);

