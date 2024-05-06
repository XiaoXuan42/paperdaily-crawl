CREATE TABLE IF NOT EXISTS paper_crawl
(
    id VARCHAR(31) NOT NULL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    abstract TEXT(65535),
    categories VARCHAR(255),
    authors VARCHAR(10002),
    published DATE,
    updated DATE
);
