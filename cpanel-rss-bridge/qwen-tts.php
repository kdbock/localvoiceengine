<?php
declare(strict_types=1);

/* Secure Qwen speech-preview relay. Upload beside qwen-vault.php. */
const PROJECT_ID = 'local-voice-engine-kdb';
const ADMIN_EMAIL = 'kristy@neusenews.com';
const CONFIG_PATH = '/home/krisdbrk/.local-voice-engine-qwen.php';
const APP_ORIGIN = 'https://local-voice-engine-kdb.web.app';
const QWEN_ENDPOINT = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation';

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: ' . APP_ORIGIN);
header('Access-Control-Allow-Headers: Authorization, Content-Type');
header('Access-Control-Allow-Methods: POST, OPTIONS');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }

function b64url_decode_safe(string $value): string { return base64_decode(strtr($value . str_repeat('=', (4 - strlen($value) % 4) % 4), '-_', '+/'), true) ?: ''; }
function fail(int $status, string $message): never { http_response_code($status); echo json_encode(['ok' => false, 'error' => $message]); exit; }
function verify_token(): void {
  $auth = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
  if (!preg_match('/^Bearer\s+(.+)$/', $auth, $match)) fail(401, 'Sign in is required.');
  $parts = explode('.', $match[1]); if (count($parts) !== 3) fail(401, 'Invalid sign-in token.');
  [$head, $body, $signature] = $parts;
  $header = json_decode(b64url_decode_safe($head), true); $payload = json_decode(b64url_decode_safe($body), true);
  if (!is_array($header) || !is_array($payload) || ($header['alg'] ?? '') !== 'RS256') fail(401, 'Invalid sign-in token.');
  if (($payload['aud'] ?? '') !== PROJECT_ID || ($payload['iss'] ?? '') !== 'https://securetoken.google.com/' . PROJECT_ID || ($payload['email'] ?? '') !== ADMIN_EMAIL || empty($payload['email_verified']) || ($payload['exp'] ?? 0) < time()) fail(403, 'Voice previews are limited to the newsroom administrator while the studio is being set up.');
  $certs = json_decode((string)file_get_contents('https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com'), true);
  $certificate = $certs[$header['kid'] ?? ''] ?? null;
  if (!$certificate || openssl_verify($head . '.' . $body, b64url_decode_safe($signature), $certificate, OPENSSL_ALGO_SHA256) !== 1) fail(401, 'Could not verify sign-in token.');
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') fail(405, 'Method not allowed.');
verify_token();
if (!is_file(CONFIG_PATH)) fail(412, 'Connect Qwen in the admin setup screen first.');
$config = require CONFIG_PATH;
$apiKey = trim((string)($config['dashscopeApiKey'] ?? ''));
if ($apiKey === '') fail(412, 'Connect Qwen in the admin setup screen first.');
$input = json_decode(file_get_contents('php://input'), true);
if (!is_array($input)) fail(400, 'Invalid voice preview request.');
$text = trim((string)($input['text'] ?? ''));
if ($text === '' || mb_strlen($text) > 600) fail(400, 'Voiceover text must be between 1 and 600 characters.');

// Built-in voices only for this first connection. Cloned brand voices will be
// registered deliberately during brand setup, not accepted from the browser.
$allowedVoices = ['Neil', 'Maia', 'Kai', 'Moon', 'Momo', 'Eldric Sage', 'Mia', 'Bellona', 'Vincent', 'Arthur', 'Seren'];
$voice = (string)($input['voice'] ?? 'Neil');
if (!in_array($voice, $allowedVoices, true)) $voice = 'Neil';
$instructions = trim((string)($input['instructions'] ?? 'Clear, warm, trustworthy local-news narration. Never theatrical.'));
if (mb_strlen($instructions) > 1600) $instructions = mb_substr($instructions, 0, 1600);
$payload = ['model' => 'qwen3-tts-instruct-flash', 'input' => ['text' => $text, 'voice' => $voice, 'language_type' => 'English', 'instructions' => $instructions, 'optimize_instructions' => true]];
$ch = curl_init(QWEN_ENDPOINT);
curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_HTTPHEADER => ['Authorization: Bearer ' . $apiKey, 'Content-Type: application/json'], CURLOPT_POSTFIELDS => json_encode($payload, JSON_UNESCAPED_UNICODE), CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 60]);
$raw = curl_exec($ch); $status = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $curlError = curl_error($ch); curl_close($ch);
if ($raw === false) fail(502, 'Qwen could not be reached: ' . ($curlError ?: 'unknown connection error'));
$result = json_decode($raw, true); $audioUrl = $result['output']['audio']['url'] ?? null;
if ($status < 200 || $status >= 300 || !is_string($audioUrl) || $audioUrl === '') { $providerMessage = is_array($result) ? ($result['message'] ?? $result['code'] ?? 'Qwen did not return audio.') : 'Qwen did not return audio.'; fail(502, 'Qwen voice preview failed: ' . $providerMessage); }
echo json_encode(['ok' => true, 'audioUrl' => $audioUrl, 'requestId' => $result['request_id'] ?? null, 'voice' => $voice]);
