DROP TABLE IF EXISTS accounts;
CREATE TABLE accounts (
	ID int(11) NOT NULL AUTO_INCREMENT,
    Username varchar(45) NOT NULL,
	Passwd varchar(45) NOT NULL,
	IsBanned tinyint(1) DEFAULT '0',
	SessionIP text,
  PRIMARY KEY (ID)
  ) AUTO_INCREMENT = 2;
  
  INSERT INTO accounts (ID, Username, Passwd, IsBanned, SessionIP) VALUES
  (1, admin, admin, 0, '');
  
  