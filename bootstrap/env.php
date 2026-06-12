<?php

/**
 * Manual .env loader — bypasses Dotenv incompatibility on this host.
 *
 * Dotenv's createImmutable() fails to find the .env file even when
 * open_basedir allows access. This file reads .env directly and
 * populates $_ENV, $_SERVER, and putenv() before Laravel boots.
 */

$envFile = __DIR__ . '/../.env';

if (file_exists($envFile) && is_readable($envFile)) {
    foreach (file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        $line = trim($line);

        // Skip comments and empty lines
        if ($line === '' || $line[0] === '#') {
            continue;
        }

        // Split on first =
        $pos = strpos($line, '=');
        if ($pos === false) {
            continue;
        }

        $key = trim(substr($line, 0, $pos));
        $value = trim(substr($line, $pos + 1), " \t\n\r\0\x0B\"'");

        putenv("$key=$value");
        $_ENV[$key] = $value;
        $_SERVER[$key] = $value;
    }
}
