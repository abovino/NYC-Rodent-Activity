-- Inspections

create table stg_rodent_inspections (
	":id"	varchar(18),
	":created_at"	timestamp with time zone,
	":updated_at"	timestamp with time zone,
	":version" varchar(17),
	inspection_type varchar(10),
	job_ticket_or_work_order_id int,
	job_id varchar(9),
	job_progress smallint,
	bbl bigint,
	boro_code smallint,
	block int,
	lot smallint,
	house_number varchar(25),
	street_name varchar(150),
	zip_code varchar(10),
	x_coord int,
	y_coord int,
	latitude float,
	longitude float,
	borough varchar(25),
	inspection_date timestamp,
	result varchar(25),
	approved_date timestamp,
	location varchar(50),
	community_board smallint,
	council_district smallint,
	census_tract int,
	bin varchar(15)
)

-- 311 Calls

-- Restaurant Inspections

-- Restaurant Violation codes

