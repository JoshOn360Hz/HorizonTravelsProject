-- MySQL dump 10.13  Distrib 9.0.1, for macos15.1 (arm64)
--
-- Host: localhost    Database: Database
-- ------------------------------------------------------
-- Server version	9.1.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `Admins`
--

DROP TABLE IF EXISTS `Admins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Admins` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Admins`
--

LOCK TABLES `Admins` WRITE;
/*!40000 ALTER TABLE `Admins` DISABLE KEYS */;
INSERT INTO `Admins` VALUES (1,'admin','$2b$12$wb6VwtVsLZ49paCLF1kUwepejWGHBWYUNtd/rldj.uMhQR03/71wi','admin@horizon.com','2024-12-28 03:10:47');
/*!40000 ALTER TABLE `Admins` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Booking_Details`
--

DROP TABLE IF EXISTS `Booking_Details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Booking_Details` (
  `ref_num` int NOT NULL AUTO_INCREMENT,
  `B_Class` int NOT NULL,
  `Econ` int NOT NULL,
  PRIMARY KEY (`ref_num`)
) ENGINE=InnoDB AUTO_INCREMENT=126 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Booking_Details`
--

LOCK TABLES `Booking_Details` WRITE;
/*!40000 ALTER TABLE `Booking_Details` DISABLE KEYS */;
INSERT INTO `Booking_Details` VALUES (95,1,0),(96,2,0),(97,1,0),(98,1,0),(99,1,0),(104,1,0),(105,1,0),(106,2,0),(107,2,0),(109,1,0),(125,1,0);
/*!40000 ALTER TABLE `Booking_Details` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Bookings`
--

DROP TABLE IF EXISTS `Bookings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Bookings` (
  `ref_num` int NOT NULL AUTO_INCREMENT,
  `a_num` int NOT NULL,
  `Fl_num_DEP` int NOT NULL,
  `Fl_num_RET` int DEFAULT NULL,
  `Payment_ID` int DEFAULT NULL,
  `departure_date` date DEFAULT NULL,
  `PAX` int NOT NULL,
  `boarding_group` varchar(50) NOT NULL DEFAULT 'error',
  PRIMARY KEY (`ref_num`),
  KEY `Fl_num_DEP` (`Fl_num_DEP`),
  KEY `Fl_num_RET` (`Fl_num_RET`),
  KEY `Bookings_ibfk_1` (`a_num`),
  KEY `FK_Bookings_Payments` (`Payment_ID`),
  CONSTRAINT `Bookings_ibfk_1` FOREIGN KEY (`a_num`) REFERENCES `Users` (`a_num`) ON DELETE CASCADE,
  CONSTRAINT `bookings_ibfk_2` FOREIGN KEY (`Fl_num_DEP`) REFERENCES `Flights` (`f_num`),
  CONSTRAINT `bookings_ibfk_3` FOREIGN KEY (`Fl_num_RET`) REFERENCES `Flights` (`f_num`),
  CONSTRAINT `FK_Bookings_Payments` FOREIGN KEY (`Payment_ID`) REFERENCES `Payments` (`payment_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_user_bookings` FOREIGN KEY (`a_num`) REFERENCES `Users` (`a_num`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=126 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Bookings`
--

LOCK TABLES `Bookings` WRITE;
/*!40000 ALTER TABLE `Bookings` DISABLE KEYS */;
INSERT INTO `Bookings` VALUES (125,18,6,NULL,78,'2025-02-12',1,'Priority');
/*!40000 ALTER TABLE `Bookings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Flight_Schedules`
--

DROP TABLE IF EXISTS `Flight_Schedules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Flight_Schedules` (
  `schedule_id` int NOT NULL AUTO_INCREMENT,
  `f_num` int NOT NULL,
  `departure_time` time NOT NULL,
  `arrival_time` time NOT NULL,
  PRIMARY KEY (`schedule_id`),
  KEY `f_num` (`f_num`),
  CONSTRAINT `flight_schedules_ibfk_1` FOREIGN KEY (`f_num`) REFERENCES `Flights` (`f_num`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Flight_Schedules`
--

LOCK TABLES `Flight_Schedules` WRITE;
/*!40000 ALTER TABLE `Flight_Schedules` DISABLE KEYS */;
INSERT INTO `Flight_Schedules` VALUES (1,1,'17:45:00','19:00:00'),(2,2,'09:00:00','10:15:00'),(3,3,'07:00:00','08:30:00'),(4,4,'12:30:00','13:30:00'),(5,5,'13:20:00','14:20:00'),(6,6,'07:40:00','08:20:00'),(7,7,'13:00:00','02:00:00'),(8,8,'12:20:00','13:30:00'),(9,9,'08:40:00','09:45:00'),(10,10,'14:30:00','15:45:00'),(11,11,'16:15:00','17:05:00'),(12,12,'18:25:00','19:13:00'),(13,13,'06:20:00','07:20:00'),(14,14,'12:00:00','14:00:00'),(15,15,'10:00:00','12:00:00'),(16,16,'18:30:00','19:30:00'),(17,17,'12:00:00','13:30:00'),(18,18,'19:00:00','20:00:00'),(19,19,'17:00:00','17:45:00'),(20,20,'07:00:00','07:45:00'),(21,21,'08:00:00','09:30:00');
/*!40000 ALTER TABLE `Flight_Schedules` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Flights`
--

DROP TABLE IF EXISTS `Flights`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Flights` (
  `f_num` int NOT NULL,
  `departure` varchar(50) NOT NULL,
  `arrival` varchar(50) NOT NULL,
  PRIMARY KEY (`f_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Flights`
--

LOCK TABLES `Flights` WRITE;
/*!40000 ALTER TABLE `Flights` DISABLE KEYS */;
INSERT INTO `Flights` VALUES (1,'Newcastle','Bristol'),(2,'Bristol','Newcastle'),(3,'Cardiff','Edinburgh'),(4,'Bristol','Manchester'),(5,'Manchester','Bristol'),(6,'Bristol','London'),(7,'London','Manchester'),(8,'Manchester','Glasgow'),(9,'Bristol','Glasgow'),(10,'Glasgow','Newcastle'),(11,'Newcastle','Manchester'),(12,'Manchester','Bristol'),(13,'Bristol','Manchester'),(14,'Portsmouth','Dundee'),(15,'Dundee','Portsmouth'),(16,'Edinburgh','Cardiff'),(17,'Southampton','Manchester'),(18,'Manchester','Southampton'),(19,'Birmingham','Newcastle'),(20,'Newcastle','Birmingham'),(21,'Aberdeen','Portsmouth');
/*!40000 ALTER TABLE `Flights` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `PAX`
--

DROP TABLE IF EXISTS `PAX`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `PAX` (
  `id` int NOT NULL AUTO_INCREMENT,
  `f_num` int NOT NULL,
  `travel_date` date NOT NULL,
  `total_passengers` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `f_num` (`f_num`,`travel_date`),
  CONSTRAINT `fk_pax_flight` FOREIGN KEY (`f_num`) REFERENCES `Flights` (`f_num`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `PAX`
--

LOCK TABLES `PAX` WRITE;
/*!40000 ALTER TABLE `PAX` DISABLE KEYS */;
/*!40000 ALTER TABLE `PAX` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Payments`
--

DROP TABLE IF EXISTS `Payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Payments` (
  `payment_id` int NOT NULL AUTO_INCREMENT,
  `card_name` varchar(100) NOT NULL,
  `card_number` varchar(16) NOT NULL,
  `expiry_date` varchar(7) DEFAULT NULL,
  `cvv` varchar(3) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `ref_num` int DEFAULT NULL,
  `refunded` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`payment_id`),
  KEY `Payments_fk_ref_num` (`ref_num`),
  CONSTRAINT `Payments_fk_ref_num` FOREIGN KEY (`ref_num`) REFERENCES `Bookings` (`ref_num`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=79 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Payments`
--

LOCK TABLES `Payments` WRITE;
/*!40000 ALTER TABLE `Payments` DISABLE KEYS */;
INSERT INTO `Payments` VALUES (4,'test','1234','2011-11','123',120.00,'2024-12-31 09:05:47',NULL,0),(22,'test','1234123412341234','2034-12','123',120.00,'2025-01-01 10:35:48',NULL,0),(38,'1234','111','2011-11','111',240.00,'2025-01-06 18:07:47',NULL,0),(39,'1','1234','2011-11','111',240.00,'2025-01-06 18:14:13',NULL,0),(54,'Josh','1234123412341234','12/34','111',440.00,'2025-01-11 01:10:52',NULL,0),(56,'1','1111111111111111','11/11','111',540.00,'2025-01-11 01:21:39',NULL,0),(74,'q','1212121212121211','12/12','123',480.00,'2025-02-05 06:48:46',NULL,0),(75,'josh','2121212121212121','12/12','121',160.00,'2025-02-05 06:49:49',NULL,0),(78,'Josh Mansfield','1234123412341234','12/34','123',160.00,'2025-02-05 09:36:36',125,0);
/*!40000 ALTER TABLE `Payments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Ticket_Info`
--

DROP TABLE IF EXISTS `Ticket_Info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Ticket_Info` (
  `ticket_id` int NOT NULL AUTO_INCREMENT,
  `f_num` int NOT NULL,
  `standard_tickets` int NOT NULL,
  `business_tickets` int NOT NULL,
  `price` decimal(8,2) NOT NULL,
  PRIMARY KEY (`ticket_id`),
  KEY `f_num` (`f_num`),
  CONSTRAINT `ticket_info_ibfk_1` FOREIGN KEY (`f_num`) REFERENCES `Flights` (`f_num`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Ticket_Info`
--

LOCK TABLES `Ticket_Info` WRITE;
/*!40000 ALTER TABLE `Ticket_Info` DISABLE KEYS */;
INSERT INTO `Ticket_Info` VALUES (1,1,104,26,90.00),(2,2,104,26,90.00),(3,3,104,26,90.00),(4,4,104,26,80.00),(5,5,104,26,80.00),(6,6,104,26,80.00),(7,7,104,26,90.00),(8,8,104,26,100.00),(9,9,104,26,110.00),(10,10,104,26,110.00),(11,11,104,26,90.00),(12,12,104,26,80.00),(13,13,104,26,80.00),(14,14,104,26,120.00),(15,15,104,26,120.00),(16,16,104,26,90.00),(17,17,104,26,90.00),(18,18,104,26,90.00),(19,19,104,26,100.00),(20,20,104,26,100.00),(21,21,104,26,100.00);
/*!40000 ALTER TABLE `Ticket_Info` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `a_num` int NOT NULL AUTO_INCREMENT,
  `f_name` varchar(50) NOT NULL,
  `l_name` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `pass` varchar(255) NOT NULL,
  `forgot_password_pin` varchar(6) NOT NULL,
  PRIMARY KEY (`a_num`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (17,'test','2','joshtest2@test.com','$2b$12$Ifh4tA1xGH3fqUEDJuyKsuR3B7EI7/5yYXx.ue4eHjgRRfIy2lITq','758268'),(18,'Josh','Mansfield','test@test.com','$2b$12$o42XDpOlJSGZRruFho1/TO5EzynmI4cxGw1JItoYXhOc5D1V8Gycm','880694'),(19,'josh','test','test3@test.com','$2b$12$0Qplvro9h5j5JLyzOk0tkOrNctPwg0GdgBybUftLnlHcB6HTYvQN.','631680');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-02-05 10:19:47
