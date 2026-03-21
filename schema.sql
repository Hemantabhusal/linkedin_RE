CREATE TABLE IF NOT EXISTS profiles (
  id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  linkedin_url VARCHAR(500) NOT NULL,
  status       ENUM('pending', 'in_progress', 'done', 'error') NOT NULL DEFAULT 'pending',
  error_msg    TEXT,
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS profile_results (
  id                             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  profile_id                     INT UNSIGNED NOT NULL UNIQUE,
  linkedin_url                   VARCHAR(500),
  first_name                     VARCHAR(200),
  last_name                      VARCHAR(200),
  headline                       TEXT,
  summary                        TEXT,
  username                       VARCHAR(200),
  sales_nav_url                  VARCHAR(500),
  country_code                   VARCHAR(10),
  country                        VARCHAR(200),
  location_name                  VARCHAR(300),
  industry                       VARCHAR(300),
  avatar_url                     TEXT,
  `current_role`                 VARCHAR(300),
  current_company                VARCHAR(300),
  current_company_linkedin_url   VARCHAR(500),
  current_company_industry       VARCHAR(300),
  current_company_linkedin_id    VARCHAR(100),
  current_company_employee_range VARCHAR(50),
  school                         VARCHAR(300),
  degree                         VARCHAR(300),
  field_of_study                 VARCHAR(300),
  activities                     TEXT,
  school_linkedin_id             VARCHAR(100),
  school_linkedin_url            VARCHAR(500),
  experiences                    JSON,
  scraped_at                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

