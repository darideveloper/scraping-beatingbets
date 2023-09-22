-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Sep 22, 2023 at 06:40 AM
-- Server version: 10.4.24-MariaDB
-- PHP Version: 8.1.6

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `beatingb_bbets`
--

-- --------------------------------------------------------

--
-- Table structure for table `apisoccer`
--

CREATE TABLE `apisoccer` (
  `id` int(11) NOT NULL,
  `id_web` varchar(50) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `country` varchar(50) DEFAULT NULL,
  `liga` varchar(50) DEFAULT NULL,
  `time` varchar(50) DEFAULT NULL,
  `team1` varchar(100) DEFAULT NULL,
  `team2` varchar(100) DEFAULT NULL,
  `score` varchar(50) DEFAULT NULL,
  `c1` varchar(10) DEFAULT NULL,
  `c2` varchar(10) DEFAULT NULL,
  `c3` varchar(10) DEFAULT NULL,
  `locemp` varchar(10) DEFAULT NULL,
  `locvis` varchar(10) DEFAULT NULL,
  `empvis` varchar(10) DEFAULT NULL,
  `over15` varchar(10) DEFAULT NULL,
  `over25` varchar(10) DEFAULT NULL,
  `under25` varchar(10) DEFAULT NULL,
  `under35` varchar(10) DEFAULT NULL,
  `ambos` varchar(10) DEFAULT NULL,
  `noambos` varchar(10) DEFAULT NULL,
  `verify` tinyint(1) DEFAULT NULL,
  `status` tinyint(1) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `apisoccer`
--
