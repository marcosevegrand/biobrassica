<?php

/**
 * cPanel-safe .env loader.
 *
 * Laravel's Dotenv file reader fails on this host, but plain file reads work.
 * So we read the file ourselves and let Dotenv parse the content string.
 */

$envFile = dirname(__DIR__).'/.env';

if (! is_file($envFile) || ! is_readable($envFile)) {
    return;
}

$contents = file_get_contents($envFile);

if ($contents === false) {
    return;
}

try {
    $variables = class_exists(\Dotenv\Dotenv::class)
        ? \Dotenv\Dotenv::parse($contents)
        : [];
} catch (Throwable) {
    $variables = [];
}

if ($variables === []) {
    foreach (preg_split('/\r\n|\r|\n/', $contents) ?: [] as $line) {
        $line = trim($line);

        if ($line === '' || str_starts_with($line, '#') || ! str_contains($line, '=')) {
            continue;
        }

        [$key, $value] = explode('=', $line, 2);
        $variables[trim($key)] = trim($value, " \t\n\r\0\x0B\"'");
    }
}

foreach ($variables as $key => $value) {
    if ($key === '') {
        continue;
    }

    $value = (string) $value;

    putenv($key.'='.$value);
    $_ENV[$key] = $value;
    $_SERVER[$key] = $value;
}
