<?php
declare(strict_types=1);

const PROJECT_ID = 'local-voice-engine-kdb';
const ADMIN_EMAIL = 'kristy@neusenews.com';
const CONFIG_PATH = '/home/krisdbrk/.local-voice-engine-qwen.php';
const APP_ORIGIN = 'https://local-voice-engine-kdb.web.app';

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: ' . APP_ORIGIN);
header('Access-Control-Allow-Headers: Authorization, Content-Type');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
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
  if (($payload['aud'] ?? '') !== PROJECT_ID || ($payload['iss'] ?? '') !== 'https://securetoken.google.com/' . PROJECT_ID || ($payload['email'] ?? '') !== ADMIN_EMAIL || empty($payload['email_verified']) || ($payload['exp'] ?? 0) < time()) fail(403, 'This vault is limited to the newsroom administrator.');
  $certs = json_decode((string)file_get_contents('https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com'), true);
  $certificate = $certs[$header['kid'] ?? ''] ?? null;
  if (!$certificate || openssl_verify($head . '.' . $body, b64url_decode_safe($signature), $certificate, OPENSSL_ALGO_SHA256) !== 1) fail(401, 'Could not verify sign-in token.');
}

verify_token();
if ($_SERVER['REQUEST_METHOD'] === 'GET') { echo json_encode(['ok' => true, 'configured' => is_file(CONFIG_PATH)]); exit; }
if ($_SERVER['REQUEST_METHOD'] !== 'POST') fail(405, 'Method not allowed.');
$input = json_decode(file_get_contents('php://input'), true); $key = trim((string)($input['apiKey'] ?? ''));
if (strlen($key) < 8 || preg_match('/[\r\n]/', $key)) fail(400, 'Enter the API key exactly as Model Studio provided it.');
$contents = "<?php\nreturn " . var_export(['dashscopeApiKey' => $key, 'updatedAt' => gmdate(DATE_ATOM)], true) . ";\n";
if (file_put_contents(CONFIG_PATH, $contents, LOCK_EX) === false) fail(500, 'Could not securely save the key.');
chmod(CONFIG_PATH, 0600);
echo json_encode(['ok' => true, 'configured' => true]);
