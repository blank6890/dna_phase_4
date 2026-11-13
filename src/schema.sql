-- Wife-Carrying World Championship database (Phase 4, Team 69)
-- Run: mysql -u <user> -p < schema.sql
DROP DATABASE IF EXISTS eukonkanto_db;
CREATE DATABASE eukonkanto_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE eukonkanto_db;

-- =====================================================================
-- Reference / strong entities
-- =====================================================================

CREATE TABLE COUNTRY (
    ISO_Code      CHAR(3)     NOT NULL,
    Country_Name  VARCHAR(60) NOT NULL,
    Continent     ENUM('Africa','Asia','Europe','North America','Oceania','South America') NOT NULL,
    CONSTRAINT pk_country PRIMARY KEY (ISO_Code),
    CONSTRAINT uq_country_name UNIQUE (Country_Name),
    CONSTRAINT ck_country_iso CHECK (ISO_Code REGEXP BINARY '^[A-Z]{3}$')
) ENGINE=InnoDB;

CREATE TABLE PERSON (
    Person_ID      INT          NOT NULL AUTO_INCREMENT,
    First_Name     VARCHAR(60)  NOT NULL,
    Last_Name      VARCHAR(60)  NOT NULL,
    Date_of_Birth  DATE         NULL,          -- Design change 2: unknown for historic champions
    Gender         ENUM('Female','Male','Other') NULL,
    Email          VARCHAR(120) NULL,
    CONSTRAINT pk_person PRIMARY KEY (Person_ID),
    CONSTRAINT uq_person_email UNIQUE (Email),
    CONSTRAINT ck_person_email CHECK (Email IS NULL OR Email LIKE '%_@_%._%'),
    CONSTRAINT ck_person_dob CHECK (Date_of_Birth IS NULL OR Date_of_Birth >= '1900-01-01'),
    INDEX ix_person_name (Last_Name, First_Name)
) ENGINE=InnoDB;

CREATE TABLE PERSON_PHONE (
    Person_ID  INT         NOT NULL,
    Phone      VARCHAR(30) NOT NULL,
    CONSTRAINT pk_person_phone PRIMARY KEY (Person_ID, Phone),
    CONSTRAINT fk_person_phone_person FOREIGN KEY (Person_ID) REFERENCES PERSON (Person_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE PERSON_CITIZENSHIP (
    Person_ID  INT     NOT NULL,
    ISO_Code   CHAR(3) NOT NULL,
    CONSTRAINT pk_person_citizenship PRIMARY KEY (Person_ID, ISO_Code),
    CONSTRAINT fk_person_citizenship_person FOREIGN KEY (Person_ID) REFERENCES PERSON (Person_ID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_person_citizenship_country FOREIGN KEY (ISO_Code) REFERENCES COUNTRY (ISO_Code)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- PERSON specialisation (Option 8A: partial, overlapping)
CREATE TABLE COMPETITOR (
    Person_ID  INT NOT NULL,
    CONSTRAINT pk_competitor PRIMARY KEY (Person_ID),
    CONSTRAINT fk_competitor_person FOREIGN KEY (Person_ID) REFERENCES PERSON (Person_ID)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE OFFICIAL (
    Person_ID        INT         NOT NULL,
    Duty_Title       VARCHAR(60) NOT NULL,
    Certified_Since  SMALLINT    NOT NULL,
    Supervisor_ID    INT         NULL,          -- recursive SUPERVISES
    CONSTRAINT pk_official PRIMARY KEY (Person_ID),
    CONSTRAINT fk_official_person FOREIGN KEY (Person_ID) REFERENCES PERSON (Person_ID)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_official_supervisor FOREIGN KEY (Supervisor_ID) REFERENCES OFFICIAL (Person_ID)
        ON DELETE RESTRICT ON UPDATE RESTRICT,   -- RESTRICT: MariaDB forbids CHECK on cascading FK columns
    CONSTRAINT ck_official_not_self CHECK (Supervisor_ID IS NULL OR Supervisor_ID <> Person_ID),
    CONSTRAINT ck_official_since CHECK (Certified_Since BETWEEN 1950 AND 2100)
) ENGINE=InnoDB;

CREATE TABLE EDITION (
    Edition_Year           SMALLINT NOT NULL,
    Championship_Level     ENUM('Finnish','World') NOT NULL,
    Start_Date             DATE     NOT NULL,
    End_Date               DATE     NOT NULL,
    Registration_Opens     DATE     NOT NULL,
    Registration_Deadline  DATETIME NOT NULL,      -- Design change 5
    CONSTRAINT pk_edition PRIMARY KEY (Edition_Year),
    CONSTRAINT ck_edition_dates CHECK (End_Date >= Start_Date),
    CONSTRAINT ck_edition_reg_window CHECK (Registration_Opens < Registration_Deadline),
    CONSTRAINT ck_edition_deadline CHECK (Registration_Deadline < Start_Date),
    CONSTRAINT ck_edition_year CHECK (YEAR(Start_Date) = Edition_Year)
) ENGINE=InnoDB;

CREATE TABLE VENUE (
    Venue_ID     INT          NOT NULL AUTO_INCREMENT,
    Venue_Name   VARCHAR(100) NOT NULL,
    Street       VARCHAR(100) NOT NULL,
    Postal_Code  VARCHAR(10)  NOT NULL,
    City         VARCHAR(60)  NOT NULL,
    CONSTRAINT pk_venue PRIMARY KEY (Venue_ID)
) ENGINE=InnoDB;

CREATE TABLE VENUE_FACILITY (
    Venue_ID  INT         NOT NULL,
    Facility  VARCHAR(60) NOT NULL,
    CONSTRAINT pk_venue_facility PRIMARY KEY (Venue_ID, Facility),
    CONSTRAINT fk_venue_facility_venue FOREIGN KEY (Venue_ID) REFERENCES VENUE (Venue_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE SERIES (
    Series_Code            VARCHAR(10)  NOT NULL,
    Series_Name            VARCHAR(60)  NOT NULL,
    Track_Length_m         DECIMAL(6,1) NOT NULL,   -- 253.5 m main track
    Water_Obstacles        TINYINT      NOT NULL,
    Dry_Obstacles          TINYINT      NOT NULL,
    Min_Carrier_Age        TINYINT      NOT NULL,
    Min_Carried_Age        TINYINT      NOT NULL,
    Min_Carried_Weight_kg  DECIMAL(4,1) NOT NULL,
    Carrier_Count          TINYINT      NOT NULL,
    Has_Heats              BOOLEAN      NOT NULL DEFAULT FALSE,   -- Design change 6
    CONSTRAINT pk_series PRIMARY KEY (Series_Code),
    CONSTRAINT uq_series_name UNIQUE (Series_Name),
    CONSTRAINT ck_series_carrier_age CHECK (Min_Carrier_Age >= 18),
    CONSTRAINT ck_series_carried_age CHECK (Min_Carried_Age >= 17),
    CONSTRAINT ck_series_weight CHECK (Min_Carried_Weight_kg >= 49),
    CONSTRAINT ck_series_carriers CHECK (Carrier_Count IN (1, 3)),
    CONSTRAINT ck_series_track CHECK (Track_Length_m > 0 AND Water_Obstacles >= 0 AND Dry_Obstacles >= 0)
) ENGINE=InnoDB;

-- RACE: weak entity owned by EDITION
CREATE TABLE RACE (
    Edition_Year     SMALLINT     NOT NULL,
    Race_No          TINYINT      NOT NULL,
    Scheduled_Start  DATETIME     NOT NULL,
    Entry_Fee_EUR    DECIMAL(8,2) NOT NULL,
    Series_Code      VARCHAR(10)  NOT NULL,
    Venue_ID         INT          NOT NULL,
    Last_Finish_At   DATETIME     NULL,             -- Design change 7
    CONSTRAINT pk_race PRIMARY KEY (Edition_Year, Race_No),
    CONSTRAINT uq_race_series UNIQUE (Edition_Year, Series_Code),   -- Design change 8
    CONSTRAINT fk_race_edition FOREIGN KEY (Edition_Year) REFERENCES EDITION (Edition_Year)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_race_series FOREIGN KEY (Series_Code) REFERENCES SERIES (Series_Code)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_race_venue FOREIGN KEY (Venue_ID) REFERENCES VENUE (Venue_ID)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_race_fee CHECK (Entry_Fee_EUR >= 0),
    CONSTRAINT ck_race_finish CHECK (Last_Finish_At IS NULL OR Last_Finish_At >= Scheduled_Start),
    INDEX ix_race_series (Series_Code)
) ENGINE=InnoDB;

CREATE TABLE ROLE (
    Role_Code  VARCHAR(10) NOT NULL,
    Role_Name  VARCHAR(40) NOT NULL,
    Leg_Order  TINYINT     NULL,
    CONSTRAINT pk_role PRIMARY KEY (Role_Code),
    CONSTRAINT ck_role_code CHECK (Role_Code IN ('CARRIER_1','CARRIER_2','CARRIER_3','CARRIED')),
    CONSTRAINT ck_role_leg CHECK ((Role_Code = 'CARRIED') = (Leg_Order IS NULL))
) ENGINE=InnoDB;

CREATE TABLE GRAND_PRIX_EVENT (
    GP_Event_ID       INT          NOT NULL AUTO_INCREMENT,
    Event_Name        VARCHAR(120) NOT NULL,
    Event_Month_Year  DATE         NOT NULL,   -- first day of the month the event is held
    City              VARCHAR(60)  NOT NULL,
    Region            VARCHAR(60)  NOT NULL,
    Organiser         VARCHAR(120) NOT NULL,
    Host_ISO_Code     CHAR(3)      NOT NULL,
    CONSTRAINT pk_gp_event PRIMARY KEY (GP_Event_ID),
    CONSTRAINT fk_gp_event_country FOREIGN KEY (Host_ISO_Code) REFERENCES COUNTRY (ISO_Code)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_gp_month CHECK (DAYOFMONTH(Event_Month_Year) = 1)
) ENGINE=InnoDB;

-- ENTRY hierarchy (Option 8C: single relation with Entry_Type)
CREATE TABLE ENTRY (
    Entry_ID                  INT          NOT NULL AUTO_INCREMENT,
    Entry_Type                ENUM('Pair','Team') NOT NULL,
    Team_Name                 VARCHAR(100) NULL,
    Represented_Organisation  VARCHAR(100) NULL,
    GP_Event_ID               INT          NULL,   -- QUALIFIES (Phase 3 FK)
    CONSTRAINT pk_entry PRIMARY KEY (Entry_ID),
    CONSTRAINT fk_entry_gp_event FOREIGN KEY (GP_Event_ID) REFERENCES GRAND_PRIX_EVENT (GP_Event_ID)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT ck_entry_team_fields CHECK (
        (Entry_Type = 'Team' AND Team_Name IS NOT NULL)
        OR (Entry_Type = 'Pair' AND Team_Name IS NULL AND Represented_Organisation IS NULL)),
    INDEX ix_entry_team (Team_Name)
) ENGINE=InnoDB;

-- Ternary PARTICIPATES_AS (PERSON, ENTRY, ROLE)
CREATE TABLE PARTICIPATES_AS (
    Entry_ID            INT          NOT NULL,
    Role_Code           VARCHAR(10)  NOT NULL,
    Person_ID           INT          NOT NULL,
    Measured_Weight_kg  DECIMAL(5,1) NULL,
    CONSTRAINT pk_participates_as PRIMARY KEY (Entry_ID, Role_Code),
    CONSTRAINT uq_participates_person UNIQUE (Entry_ID, Person_ID),
    CONSTRAINT fk_participates_as_entry FOREIGN KEY (Entry_ID) REFERENCES ENTRY (Entry_ID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_participates_as_role FOREIGN KEY (Role_Code) REFERENCES ROLE (Role_Code)
        ON DELETE RESTRICT ON UPDATE RESTRICT,   -- RESTRICT: Role_Code is used in ck_participates_weight
    CONSTRAINT fk_participates_as_person FOREIGN KEY (Person_ID) REFERENCES PERSON (Person_ID)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_participates_weight CHECK (
        Measured_Weight_kg IS NULL OR (Role_Code = 'CARRIED' AND Measured_Weight_kg > 0))
) ENGINE=InnoDB;

CREATE TABLE REPRESENTS (
    Entry_ID  INT     NOT NULL,
    ISO_Code  CHAR(3) NOT NULL,
    CONSTRAINT pk_represents PRIMARY KEY (Entry_ID, ISO_Code),
    CONSTRAINT fk_represents_entry FOREIGN KEY (Entry_ID) REFERENCES ENTRY (Entry_ID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_represents_country FOREIGN KEY (ISO_Code) REFERENCES COUNTRY (ISO_Code)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE REGISTRATION (
    Registration_ID  INT          NOT NULL AUTO_INCREMENT,
    Bib_No           SMALLINT     NULL,            -- Design change 3: NULL once cancelled
    Registered_At    DATETIME     NOT NULL,
    Cancelled_At     DATETIME     NULL,
    Payment_Status   ENUM('Pending','Paid','Refunded') NOT NULL,
    Fee_Paid_EUR     DECIMAL(8,2) NOT NULL,
    Entry_ID         INT          NOT NULL,
    Edition_Year     SMALLINT     NOT NULL,
    Race_No          TINYINT      NOT NULL,
    CONSTRAINT pk_registration PRIMARY KEY (Registration_ID),
    CONSTRAINT uq_reg_bib UNIQUE (Edition_Year, Bib_No),
    CONSTRAINT uq_reg_entry_race UNIQUE (Entry_ID, Edition_Year, Race_No),
    CONSTRAINT fk_registration_entry FOREIGN KEY (Entry_ID) REFERENCES ENTRY (Entry_ID)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_registration_race FOREIGN KEY (Edition_Year, Race_No) REFERENCES RACE (Edition_Year, Race_No)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_registration_bib CHECK (Bib_No IS NULL OR Bib_No > 0),
    CONSTRAINT ck_registration_fee CHECK (Fee_Paid_EUR >= 0),
    CONSTRAINT ck_registration_cancel_bib CHECK (Cancelled_At IS NULL OR Bib_No IS NULL),
    CONSTRAINT ck_registration_cancel_time CHECK (Cancelled_At IS NULL OR Cancelled_At >= Registered_At),
    INDEX ix_registration_race (Edition_Year, Race_No)
) ENGINE=InnoDB;

-- RESULT: weak entity owned by REGISTRATION
CREATE TABLE RESULT (
    Registration_ID          INT          NOT NULL,
    Stage                    ENUM('Heat 1','Heat 2','Heat 3','Final','Single') NOT NULL,
    Raw_Time_s               DECIMAL(7,2) NULL,
    Status                   ENUM('Finished','DNS','DNF','DQ') NOT NULL,
    Recorded_By_Official_ID  INT          NULL,
    CONSTRAINT pk_result PRIMARY KEY (Registration_ID, Stage),
    CONSTRAINT fk_result_registration FOREIGN KEY (Registration_ID) REFERENCES REGISTRATION (Registration_ID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_result_official FOREIGN KEY (Recorded_By_Official_ID) REFERENCES OFFICIAL (Person_ID)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT ck_result_time_status CHECK ((Status = 'Finished') = (Raw_Time_s IS NOT NULL)),
    CONSTRAINT ck_result_time_positive CHECK (Raw_Time_s IS NULL OR Raw_Time_s > 0)
) ENGINE=InnoDB;

-- PENALTY: weak entity owned by RESULT
CREATE TABLE PENALTY (
    Registration_ID  INT          NOT NULL,
    Stage            ENUM('Heat 1','Heat 2','Heat 3','Final','Single') NOT NULL,
    Penalty_No       TINYINT      NOT NULL,
    Adjustment_Type  ENUM('Penalty','Bonus','Warning') NOT NULL,
    Seconds          DECIMAL(6,2) NOT NULL,
    Reason           VARCHAR(200) NOT NULL,
    CONSTRAINT pk_penalty PRIMARY KEY (Registration_ID, Stage, Penalty_No),
    CONSTRAINT fk_penalty_result FOREIGN KEY (Registration_ID, Stage) REFERENCES RESULT (Registration_ID, Stage)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT ck_penalty_seconds CHECK (
        (Adjustment_Type = 'Warning' AND Seconds = 0)
        OR (Adjustment_Type IN ('Penalty','Bonus') AND Seconds > 0)),
    CONSTRAINT ck_penalty_no CHECK (Penalty_No > 0)
) ENGINE=InnoDB;

CREATE TABLE PROTEST (
    Protest_ID    INT          NOT NULL AUTO_INCREMENT,
    Filed_At      DATETIME     NOT NULL,
    Reason        VARCHAR(500) NOT NULL,
    Outcome       ENUM('Pending','Upheld','Rejected') NOT NULL DEFAULT 'Pending',
    Decided_At    DATETIME     NULL,
    Entry_ID      INT          NOT NULL,
    Edition_Year  SMALLINT     NOT NULL,
    Race_No       TINYINT      NOT NULL,
    CONSTRAINT pk_protest PRIMARY KEY (Protest_ID),
    CONSTRAINT fk_protest_entry FOREIGN KEY (Entry_ID) REFERENCES ENTRY (Entry_ID)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_protest_race FOREIGN KEY (Edition_Year, Race_No) REFERENCES RACE (Edition_Year, Race_No)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_protest_decided CHECK ((Outcome = 'Pending') = (Decided_At IS NULL)),
    CONSTRAINT ck_protest_order CHECK (Decided_At IS NULL OR Decided_At >= Filed_At),
    INDEX ix_protest_outcome (Outcome)
) ENGINE=InnoDB;

CREATE TABLE DECIDES (
    Official_ID  INT NOT NULL,
    Protest_ID   INT NOT NULL,
    Vote         ENUM('Uphold','Reject') NOT NULL,
    CONSTRAINT pk_decides PRIMARY KEY (Official_ID, Protest_ID),
    CONSTRAINT fk_decides_official FOREIGN KEY (Official_ID) REFERENCES OFFICIAL (Person_ID)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_decides_protest FOREIGN KEY (Protest_ID) REFERENCES PROTEST (Protest_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE OFFICIATES_IN (
    Official_ID   INT         NOT NULL,
    Edition_Year  SMALLINT    NOT NULL,
    Race_No       TINYINT     NOT NULL,
    Duty          ENUM('Jury','Timekeeper','Starter','Info desk') NOT NULL,
    CONSTRAINT pk_officiates_in PRIMARY KEY (Official_ID, Edition_Year, Race_No),
    CONSTRAINT fk_officiates_in_official FOREIGN KEY (Official_ID) REFERENCES OFFICIAL (Person_ID)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_officiates_in_race FOREIGN KEY (Edition_Year, Race_No) REFERENCES RACE (Edition_Year, Race_No)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE PRIZE (
    Prize_ID        INT          NOT NULL AUTO_INCREMENT,
    Prize_Name      VARCHAR(80)  NOT NULL,
    Prize_Type      ENUM('Placement','Special') NOT NULL,
    Placement_Rank  TINYINT      NULL,
    Includes_Drink  BOOLEAN      NOT NULL DEFAULT FALSE,
    Description     VARCHAR(300) NULL,
    Prize_Scope     ENUM('Series','Weekend') NOT NULL,
    CONSTRAINT pk_prize PRIMARY KEY (Prize_ID),
    CONSTRAINT uq_prize_name UNIQUE (Prize_Name),
    CONSTRAINT ck_prize_rank CHECK (
        (Prize_Type = 'Placement' AND Placement_Rank BETWEEN 1 AND 3)
        OR (Prize_Type = 'Special' AND Placement_Rank IS NULL))
) ENGINE=InnoDB;

CREATE TABLE AWARDED (
    Prize_ID         INT  NOT NULL,
    Registration_ID  INT  NOT NULL,
    Awarded_On       DATE NOT NULL,
    CONSTRAINT pk_awarded PRIMARY KEY (Prize_ID, Registration_ID),
    CONSTRAINT fk_awarded_prize FOREIGN KEY (Prize_ID) REFERENCES PRIZE (Prize_ID)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_awarded_registration FOREIGN KEY (Registration_ID) REFERENCES REGISTRATION (Registration_ID)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE OFFERS (
    Series_Code  VARCHAR(10) NOT NULL,
    Prize_ID     INT         NOT NULL,
    CONSTRAINT pk_offers PRIMARY KEY (Series_Code, Prize_ID),
    CONSTRAINT fk_offers_series FOREIGN KEY (Series_Code) REFERENCES SERIES (Series_Code)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_offers_prize FOREIGN KEY (Prize_ID) REFERENCES PRIZE (Prize_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE SPONSOR (
    Sponsor_ID    INT          NOT NULL AUTO_INCREMENT,
    Sponsor_Name  VARCHAR(100) NOT NULL,
    Website_URL   VARCHAR(200) NULL,
    CONSTRAINT pk_sponsor PRIMARY KEY (Sponsor_ID),
    CONSTRAINT uq_sponsor_name UNIQUE (Sponsor_Name),
    CONSTRAINT ck_sponsor_url CHECK (Website_URL IS NULL OR Website_URL LIKE 'http%')
) ENGINE=InnoDB;

CREATE TABLE SPONSORS (
    Sponsor_ID    INT      NOT NULL,
    Edition_Year  SMALLINT NOT NULL,
    CONSTRAINT pk_sponsors PRIMARY KEY (Sponsor_ID, Edition_Year),
    CONSTRAINT fk_sponsors_sponsor FOREIGN KEY (Sponsor_ID) REFERENCES SPONSOR (Sponsor_ID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_sponsors_edition FOREIGN KEY (Edition_Year) REFERENCES EDITION (Edition_Year)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE VENDOR (
    Vendor_ID      INT          NOT NULL AUTO_INCREMENT,
    Business_Name  VARCHAR(100) NOT NULL,
    Contact_Name   VARCHAR(100) NOT NULL,
    Phone          VARCHAR(30)  NOT NULL,
    Email          VARCHAR(120) NOT NULL,
    CONSTRAINT pk_vendor PRIMARY KEY (Vendor_ID),
    CONSTRAINT uq_vendor_name UNIQUE (Business_Name),
    CONSTRAINT ck_vendor_email CHECK (Email LIKE '%_@_%._%')
) ENGINE=InnoDB;

CREATE TABLE VENDOR_PRODUCT_CATEGORY (
    Vendor_ID  INT NOT NULL,
    Category   ENUM('Food','Handicrafts','Local specialities') NOT NULL,
    CONSTRAINT pk_vendor_product_category PRIMARY KEY (Vendor_ID, Category),
    CONSTRAINT fk_vendor_product_category_vendor FOREIGN KEY (Vendor_ID) REFERENCES VENDOR (Vendor_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE EXHIBITS_AT (
    Vendor_ID             INT          NOT NULL,
    Edition_Year          SMALLINT     NOT NULL,
    Booth_Size            ENUM('4x4','4x8','Custom') NOT NULL,
    Booth_Fee_EUR         DECIMAL(8,2) NOT NULL,
    Electricity_Required  BOOLEAN      NOT NULL DEFAULT FALSE,
    Paid                  BOOLEAN      NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_exhibits_at PRIMARY KEY (Vendor_ID, Edition_Year),
    CONSTRAINT fk_exhibits_at_vendor FOREIGN KEY (Vendor_ID) REFERENCES VENDOR (Vendor_ID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_exhibits_at_edition FOREIGN KEY (Edition_Year) REFERENCES EDITION (Edition_Year)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_exhibits_at_fee CHECK (Booth_Fee_EUR >= 0)
) ENGINE=InnoDB;
