import http from "k6/http";
import { sleep } from "k6";

export const options = {
  vus: 10,
  duration: "30s",
};

const baseUrl = __ENV.BASE_URL || "http://localhost:8003";
const itemId = __ENV.ITEM_ID || "1";
const login = __ENV.LOGIN || "loadtest";
const password = __ENV.PASSWORD || "loadtest";

let sessionReady = false;

function ensureSession() {
  if (sessionReady) return;
  const res = http.post(
    `${baseUrl}/login`,
    JSON.stringify({ login, password }),
    { headers: { "Content-Type": "application/json" } }
  );
  if (res.status !== 200) {
    throw new Error(`login failed: ${res.status} ${res.body}`);
  }
  sessionReady = true;
}

export default function () {
  ensureSession();

  http.post(
    `${baseUrl}/simple_predict`,
    JSON.stringify({ item_id: Number(itemId) }),
    { headers: { "Content-Type": "application/json" } }
  );

  http.post(`${baseUrl}/async_predict?item_id=${itemId}`);
  http.get(`${baseUrl}/moderation_result/999999`);
  sleep(1);
}
