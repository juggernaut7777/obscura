// background.js v6.0 — Elite Token Bridge
// Architecture reverse-engineered from G-Labs Auth Helper v3.0.0
// Key innovations: on-demand tokens, dynamic site-key, auto-tab, keep-alive

const BRIDGE_URL = "http://127.0.0.1:9877";
const POLL_INTERVAL = 1500;   // Check bridge every 1.5s
const HEARTBEAT_MIN  = 1;     // Passive push every 60s

let isPolling  = false;
let tokenCount = 0;
let lastPush   = 0;

async function extLog(msg) {
    console.log(`[OBSCURA v6] ${msg}`);
    try {
        fetch(`${BRIDGE_URL}/ext-status`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ msg: String(msg) })
        }).catch(() => {});
    } catch(e) {}
}
// Chrome kills idle service workers after 30s.
// Alarms + heartbeat keep it permanently alive (G-Labs technique).

chrome.alarms.create("keepAlive",  { periodInMinutes: 0.4 });   // 24s
chrome.alarms.create("heartbeat",  { periodInMinutes: HEARTBEAT_MIN });

chrome.alarms.onAlarm.addListener(async (alarm) => {
    if (alarm.name === "keepAlive" && !isPolling) startPolling();
    if (alarm.name === "heartbeat") await generateAndPushToken(false, "IMAGE_GENERATION");
});

chrome.runtime.onInstalled.addListener(() => startPolling());
chrome.runtime.onStartup.addListener(() => startPolling());

// Auto-detect when user navigates to Flow
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === "complete" && tab.url && (tab.url.includes("flow.google") || tab.url.includes("labs.google"))) {
        if (!isPolling) startPolling();
        generateAndPushToken(false, "IMAGE_GENERATION");
    }
});

console.log("🟢 [OBSCURA v6] Elite Token Bridge started.");
startPolling();
generateAndPushToken(false, "IMAGE_GENERATION");

// ─── 2. BRIDGE POLLING (ON-DEMAND TOKENS) ───────────────────────
// Instead of blindly pushing tokens every 3s (which got us flagged),
// we now ASK the bridge "do you need a fresh token right now?"
// Only when it says yes do we generate one — maximum freshness.

async function startPolling() {
    if (isPolling) return;
    isPolling = true;
    console.log("🔄 [OBSCURA v6] Polling bridge for on-demand token requests...");

    while (isPolling) {
        try {
            const resp = await fetch(`${BRIDGE_URL}/need-token`, {
                signal: AbortSignal.timeout(3000)
            });

             if (resp.ok) {
                 const data = await resp.json();
                 if (data.pendingGeneration) {
                     console.log("🎬 [OBSCURA v6] Bridge requested in-browser video generation:", data.pendingGeneration);
                     await generateVideoInBrowser(data.pendingGeneration);
                 } else if (data.need) {
                     if (data.action === "RELOAD") {
                         console.log("🔄 [OBSCURA v6] Bridge requested reload. Reloading extension...");
                         chrome.runtime.reload();
                         return;
                     }
                     console.log(`⚡ [OBSCURA v6] Bridge needs FRESH token for ${data.action}! Generating NOW...`);
                     await generateAndPushToken(true, data.action || "IMAGE_GENERATION");
                 }
             }
        } catch (e) {
            // Bridge not running — that's fine, we'll keep trying
        }

        await sleep(POLL_INTERVAL);
    }
}

// ─── 3. TOKEN GENERATION (THE CORE) ─────────────────────────────
// Uses chrome.scripting.executeScript in MAIN world (G-Labs technique).
// This lets us access Google's internal grecaptcha object directly
// from the background worker — no content script spam needed.

async function generateAndPushToken(forceOpen = false, action = "IMAGE_GENERATION") {
    let tabId = await findFlowTab();
    if (!tabId) {
        try {
            const allTabs = await chrome.tabs.query({});
            const urls = allTabs.map(t => (t.title || "tab") + " [" + (t.url || t.pendingUrl || "no-url") + "]").slice(0, 5).join(" ; ");
            await extLog(`ℹ️ Waiting for Flow tab. Detected browser tabs: ${urls}`);
        } catch (err) {
            await extLog("ℹ️ No Flow tab found.");
        }
        return;
    }
    await extLog(`🔍 Found Flow tab ${tabId}. Generating fresh token for ${action}...`);

    try {
        // Softly activate tab if not already active
        try {
            const tab = await chrome.tabs.get(tabId);
            if (tab && !tab.active) {
                await chrome.tabs.update(tabId, { active: true });
                console.log(`👁️ [OBSCURA v6] Activated Flow tab ${tabId}.`);
                await sleep(1000);
            }
        } catch (e) {
            // Non-critical
        }

        let bgSessionToken = null;
        let bgUserName = null;
        const authCandidates = [
            "https://labs.google/fx/api/auth/session",
            "https://flow.google.com/fx/api/auth/session"
        ];
        for (const ep of authCandidates) {
            try {
                const res = await fetch(ep, { credentials: "include" });
                if (res.ok) {
                    const text = await res.text();
                    if (text.trim().startsWith("{")) {
                        const parsed = JSON.parse(text);
                        if (parsed.access_token) {
                            bgSessionToken = parsed.access_token;
                            bgUserName = parsed.user?.name || "GoogleUser";
                            await extLog(`✅ Background auth fetch succeeded from ${ep}!`);
                            break;
                        }
                    }
                } else {
                    await extLog(`BG auth fetch from ${ep} returned ${res.status}`);
                }
            } catch (err) {
                await extLog(`BG auth fetch from ${ep} error: ${err.message}`);
            }
        }

        const results = await chrome.scripting.executeScript({
            target: { tabId },
            world: "MAIN",
            args: [ action, bgSessionToken, bgUserName ],
            func: async (action, bgToken, bgUser) => {
                try {
                    // ── Step 1: Bearer token ──
                    let auth = bgToken ? { access_token: bgToken, user: { name: bgUser } } : null;
                    const authCandidates = [
                        "https://labs.google/fx/api/auth/session",
                        "/fx/api/auth/session",
                        "/api/auth/session",
                        "https://flow.google.com/api/auth/session",
                        "https://flow.google.com/fx/api/auth/session"
                    ];
                    let attemptsDiag = [];
                    for (const url of authCandidates) {
                        try {
                            const res = await fetch(url, { credentials: "include" });
                            attemptsDiag.push(`${url}=${res.status}`);
                            if (res.ok) {
                                const text = await res.text();
                                if (text.trim().startsWith("{")) {
                                    const parsed = JSON.parse(text);
                                    if (parsed.access_token) {
                                        auth = parsed;
                                        break;
                                    }
                                }
                            }
                        } catch(e) {
                            attemptsDiag.push(`${url}=err:${e.message}`);
                        }
                    }

                    if (!auth || !auth.access_token) {
                        // Scan localStorage & sessionStorage for Google OAuth bearer tokens
                        try {
                            for (let i = 0; i < localStorage.length; i++) {
                                const val = localStorage.getItem(localStorage.key(i));
                                if (val && val.includes("ya29.")) {
                                    const m = val.match(/(ya29\.[a-zA-Z0-9_\-]+)/);
                                    if (m) { auth = { access_token: m[1], user: { name: "GoogleUser" } }; break; }
                                }
                            }
                        } catch(e) {}
                        if (!auth || !auth.access_token) {
                            try {
                                for (let i = 0; i < sessionStorage.length; i++) {
                                    const val = sessionStorage.getItem(sessionStorage.key(i));
                                    if (val && val.includes("ya29.")) {
                                        const m = val.match(/(ya29\.[a-zA-Z0-9_\-]+)/);
                                        if (m) { auth = { access_token: m[1], user: { name: "GoogleUser" } }; break; }
                                    }
                                }
                            } catch(e) {}
                        }
                    }

                    if (!auth || !auth.access_token) {
                        return { error: `No access_token found. Attempts: ${attemptsDiag.join(", ")}` };
                    }

                    // ── Step 2: Dynamic reCAPTCHA site-key (G-Labs technique) ──
                    let siteKey = null;

                    // Method A: Extract from grecaptcha internal config (deep scan)
                    let siteKeysFound = [];
                    let siteKeyMethod = "NONE";
                    let cfgDiag = "NOT_FOUND";
                    try {
                        if (typeof ___grecaptcha_cfg !== "undefined") {
                            const cfg = ___grecaptcha_cfg;
                            const clientKeys = cfg.clients ? Object.keys(cfg.clients) : [];
                            cfgDiag = `clients=${clientKeys.length},keys=[${clientKeys.join(",")}]`;
                            
                            // Deep scan: walk 4 levels deep to find any sitekey property
                            const walk = (obj, depth, path) => {
                                if (!obj || typeof obj !== "object" || depth > 4) return;
                                for (const k of Object.keys(obj)) {
                                    try {
                                        const v = obj[k];
                                        if (k === "sitekey" && typeof v === "string") {
                                            if (!siteKeysFound.includes(v)) {
                                                siteKeysFound.push(v);
                                                console.log(`🔍 [OBSCURA v6] Found sitekey at ${path}.${k}: ${v}`);
                                            }
                                        } else if (v && typeof v === "object") {
                                            walk(v, depth + 1, `${path}.${k}`);
                                        }
                                    } catch (e) {}
                                }
                            };
                            
                            if (cfg.clients) {
                                for (const ckey of clientKeys) {
                                    walk(cfg.clients[ckey], 0, `clients[${ckey}]`);
                                }
                            }
                            
                            if (siteKeysFound.length > 0) {
                                siteKey = siteKeysFound[0];
                                siteKeyMethod = "A_CFG";
                            }
                        }
                    } catch (e) {
                        cfgDiag = "ERROR:" + e.message;
                    }

                    // Method B: Extract from script tags
                    if (!siteKey) {
                        try {
                            const scripts = document.querySelectorAll('script[src*="recaptcha"]');
                            for (const el of scripts) {
                                const m = el.src.match(/[?&]render=([^&]+)/);
                                if (m && m[1] !== "explicit") {
                                    siteKey = m[1];
                                    siteKeyMethod = "B_SCRIPT";
                                    break;
                                }
                            }
                        } catch (e) {}
                    }

                    // Method C: Hardcoded fallback removed for security.
                    if (!siteKey) {
                        console.error("🔍 [OBSCURA v6] Failed to resolve siteKey dynamically. Extension functionality may be limited.");
                        siteKeyMethod = "FAILED";
                    }
                    
                    console.log(`🔍 [OBSCURA v6] siteKey resolved via ${siteKeyMethod}. cfgDiag=${cfgDiag}. allKeys=[${siteKeysFound.join(",")}]`);

                    // Helper to simulate basic human interactions and generate telemetry
                    const simulateUserTelemetry = async () => {
                        try {
                            const start = Date.now();
                            while (Date.now() - start < 4000) {
                                const x = Math.floor(Math.random() * window.innerWidth);
                                const y = Math.floor(Math.random() * window.innerHeight);
                                const moveEvent = new MouseEvent("mousemove", {
                                    clientX: x,
                                    clientY: y,
                                    bubbles: true,
                                    cancelable: true
                                });
                                document.dispatchEvent(moveEvent);
                                
                                if (Math.random() > 0.8) {
                                    window.scrollBy(0, Math.random() > 0.5 ? 5 : -5);
                                }
                                await new Promise(r => setTimeout(r, 100));
                            }
                            const clickEvent = new MouseEvent("click", {
                                clientX: Math.floor(Math.random() * 100),
                                clientY: Math.floor(Math.random() * 100),
                                bubbles: true,
                                cancelable: true
                            });
                            document.body.dispatchEvent(clickEvent);
                            console.log("⚡ [OBSCURA v6] Simulated extended user telemetry.");
                        } catch (err) {
                            console.log("⚠️ [OBSCURA v6] Telemetry simulation error:", err);
                        }
                    };

                    // ── Step 3: Generate reCAPTCHA token ──
                    let recaptchaToken = "NONE";
                    if (typeof grecaptcha !== "undefined" && grecaptcha.enterprise) {
                        await simulateUserTelemetry();
                        await new Promise(r => grecaptcha.enterprise.ready(r));
                        recaptchaToken = await grecaptcha.enterprise.execute(siteKey, {
                            action: action
                        });
                    }

                    let pid = window.location.href.match(/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/i)?.[1];
                    if (!pid) {
                        try {
                            for (let i = 0; i < localStorage.length; i++) {
                                const val = localStorage.getItem(localStorage.key(i));
                                const m = val && val.match(/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/i);
                                if (m) { pid = m[1]; break; }
                            }
                        } catch(e) {}
                    }
                    pid = pid || "NOT_FOUND";
                    
                    return {
                        bearer: auth.access_token,
                        recaptcha: recaptchaToken,
                        user: auth.user?.name || "unknown",
                        siteKey: siteKey,
                        siteKeyMethod: siteKeyMethod,
                        cfgDiag: cfgDiag,
                        allSiteKeys: siteKeysFound,
                        projectId: pid,
                        action: action
                    };
                } catch (e) {
                    return { error: e.message || String(e) };
                }
            }
        });

        if (results && results[0] && results[0].result) {
            const data = results[0].result;

            if (data.error) {
                await extLog(`❌ Token gen in-page error: ${data.error}`);
                return;
            }

            // Push to bridge
            const pushResp = await fetch(`${BRIDGE_URL}/push`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            });

            if (pushResp.ok) {
                tokenCount++;
                lastPush = Date.now();
                chrome.storage.local.set({ tokenCount, lastPush });
                await extLog(`✅ Fresh token #${tokenCount} pushed to bridge (User: ${data.user}, Project: ${data.projectId})`);
            } else {
                await extLog(`⚠️ Bridge responded with HTTP ${pushResp.status} on /push`);
            }
        } else {
            await extLog(`⚠️ Script execution returned empty result: ${JSON.stringify(results)}`);
        }
    } catch (e) {
        await extLog(`⚠️ Script injection failed: ${e.message}`);
    }
}

// ─── 4. TAB MANAGEMENT (STRICT SINGLE-TAB + DEDUPLICATION) ─────────

let isOpeningTab = false;
let lastTabOpenTime = 0;
const TAB_OPEN_COOLDOWN = 60000; // 60s cooldown between auto-open attempts

async function findFlowTab() {
    try {
        const tabs = await chrome.tabs.query({});
        
        // Priority 1: Flow project or tools page (match url or pendingUrl)
        const flowTabs = tabs.filter(t => {
            const u = (t.url || t.pendingUrl || "").toLowerCase();
            return (u.includes("/tools/flow") || u.includes("labs.google/fx") || u.includes("/flow")) && !u.includes("accounts.google.com");
        });

        if (flowTabs.length > 0) {
            // Deduplicate: If multiple Flow tabs exist, keep ONLY the first one and close the rest
            if (flowTabs.length > 1) {
                const extraIds = flowTabs.slice(1).map(t => t.id).filter(Boolean);
                if (extraIds.length > 0) {
                    chrome.tabs.remove(extraIds).catch(() => {});
                    console.log(`🧹 [OBSCURA v6] Closed ${extraIds.length} duplicate Flow tab(s). Keeping tab ${flowTabs[0].id}.`);
                }
            }
            return flowTabs[0].id;
        }

        // Priority 2: Any labs.google page
        const labsTabs = tabs.filter(t => {
            const u = (t.url || t.pendingUrl || "").toLowerCase();
            return u.includes("labs.google") && !u.includes("accounts.google.com");
        });

        if (labsTabs.length > 0) {
            if (labsTabs.length > 1) {
                const extraIds = labsTabs.slice(1).map(t => t.id).filter(Boolean);
                if (extraIds.length > 0) {
                    chrome.tabs.remove(extraIds).catch(() => {});
                    console.log(`🧹 [OBSCURA v6] Closed ${extraIds.length} duplicate labs.google tab(s).`);
                }
            }
            return labsTabs[0].id;
        }

        return null;
    } catch (e) {
        return null;
    }
}

async function autoOpenFlowTab() {
    // Tab auto-creation is permanently disabled to prevent Chrome tab spam.
    // The extension passively uses the Flow tab already opened by the user.
    return await findFlowTab();
}

// ─── 5. UTILITY ──────────────────────────────────────────────────

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ─── 6. IN-BROWSER GENERATION ROUTING ────────────────────────────

async function generateVideoInBrowser(genData) {
    const tabId = await findFlowTab();
    if (!tabId) {
        console.log("⚠️ [OBSCURA v6] No Flow tab found for in-browser video generation.");
        await fetch(`${BRIDGE_URL}/push-generation-result`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ error: "no active Google Flow tab found in Chrome" })
        });
        return;
    }

    try {
        // Step 1: Foreground the tab
        try {
            const tab = await chrome.tabs.get(tabId);
            if (tab) {
                await chrome.tabs.update(tabId, { active: true });
                await chrome.windows.update(tab.windowId, { focused: true, state: "normal" });
                console.log(`👁️ [OBSCURA v6] Activated Flow tab ${tabId} for video generation.`);
                await sleep(2000);
            }
        } catch (e) {}

        // Step 2: Generate reCAPTCHA token using IMAGE_GENERATION (always active and high score since tab is focused)
        const authResults = await chrome.scripting.executeScript({
            target: { tabId },
            world: "MAIN",
            func: async () => {
                try {
                    const authReq = await fetch("/fx/api/auth/session", { credentials: "include" });
                    if (!authReq.ok) return { error: "Auth fetch failed: " + authReq.status };
                    const auth = await authReq.json();
                    
                    let siteKey = "";
                    if (typeof ___grecaptcha_cfg !== "undefined" && ___grecaptcha_cfg.clients) {
                        const clients = ___grecaptcha_cfg.clients;
                        for (const key of Object.keys(clients)) {
                            const client = clients[key];
                            for (const prop of Object.keys(client)) {
                                const val = client[prop];
                                if (val && typeof val === "object") {
                                    for (const p2 of Object.keys(val)) {
                                        const v2 = val[p2];
                                        if (v2 && typeof v2 === "object" && v2.sitekey) {
                                            siteKey = v2.sitekey;
                                            break;
                                        }
                                    }
                                }
                            }
                        }
                    }
                    const pid = window.location.href.split('/project/')[1]?.split('/')[0] || "NOT_FOUND";
                    return { bearer: auth.access_token, siteKey: siteKey, projectId: pid };
                } catch (e) {
                    return { error: e.message || String(e) };
                }
            }
        });

        if (!authResults || !authResults[0] || !authResults[0].result || authResults[0].result.error) {
            throw new Error(authResults?.[0]?.result?.error || "failed to retrieve auth session");
        }

        const { bearer, siteKey, projectId } = authResults[0].result;

        // Execute telemetry simulation inside page
        await chrome.scripting.executeScript({
            target: { tabId },
            world: "MAIN",
            func: async () => {
                try {
                    const start = Date.now();
                    while (Date.now() - start < 3000) {
                        const x = Math.floor(Math.random() * window.innerWidth);
                        const y = Math.floor(Math.random() * window.innerHeight);
                        const moveEvent = new MouseEvent("mousemove", { clientX: x, clientY: y, bubbles: true, cancelable: true });
                        document.dispatchEvent(moveEvent);
                        if (Math.random() > 0.8) {
                            window.scrollBy(0, Math.random() > 0.5 ? 5 : -5);
                        }
                        await new Promise(r => setTimeout(r, 100));
                    }
                    const clickEvent = new MouseEvent("click", { clientX: 10, clientY: 10, bubbles: true, cancelable: true });
                    document.body.dispatchEvent(clickEvent);
                    console.log("⚡ [OBSCURA v6] Simulated video telemetry.");
                } catch (e) {}
            }
        });

        // Generate reCAPTCHA token inside page
        const rcResult = await chrome.scripting.executeScript({
            target: { tabId },
            world: "MAIN",
            args: [ siteKey, genData.action || "VIDEO_GENERATION" ],
            func: async (siteKey, reqAction) => {
                if (typeof grecaptcha !== "undefined" && grecaptcha.enterprise) {
                    await new Promise(r => grecaptcha.enterprise.ready(r));
                    return await grecaptcha.enterprise.execute(siteKey, { action: reqAction });
                }
                return "NONE";
            }
        });

        const recaptcha = rcResult?.[0]?.result || "NONE";

        // Step 3: Run the fetch call inside the page context
        console.log("🚀 [OBSCURA v6] Launching fetch inside page context...");
        const apiResults = await chrome.scripting.executeScript({
            target: { tabId },
            world: "MAIN",
            args: [ bearer, recaptcha, projectId, genData ],
            func: async (bearer, recaptcha, projectId, genData) => {
                try {
                    const payload = {
                        "mediaGenerationContext": {
                            "batchId": crypto.randomUUID ? crypto.randomUUID() : "a0f095d8-c26a-4731-8bd9-79e6d59754b1",
                            "audioFailurePreference": "BLOCK_SILENCED_VIDEOS"
                        },
                        "clientContext": {
                            "projectId": projectId,
                            "tool": "PINHOLE",
                            "userPaygateTier": "PAYGATE_TIER_ONE",
                            "sessionId": ";" + Date.now(),
                            "recaptchaContext": {
                                "token": recaptcha,
                                "applicationType": "RECAPTCHA_APPLICATION_TYPE_WEB"
                            }
                        },
                        "requests": [{
                            "aspectRatio": genData.aspectRatio,
                            "videoModelKey": "veo_3_1_t2v_lite",
                            "seed": Math.floor(Math.random() * 999999),
                            "textInput": {
                                "structuredPrompt": {
                                    "parts": [{"text": genData.prompt}]
                                }
                            },
                            "metadata": {}
                        }],
                        "useV2ModelConfig": true
                    };
                    
                    const resp = await fetch("https://aisandbox-pa.googleapis.com/v1/video:batchAsyncGenerateVideoText", {
                        method: "POST",
                        headers: {
                            "Authorization": "Bearer " + bearer,
                            "Content-Type": "text/plain;charset=UTF-8",
                            "Referer": "https://labs.google/"
                        },
                        body: JSON.stringify(payload)
                    });
                    
                    if (!resp.ok) {
                        return { error: `HTTP ${resp.status}: ${await resp.text()}` };
                    }
                    return await resp.json();
                } catch (err) {
                    return { error: err.message || String(err) };
                }
            }
        });

        const apiResponse = apiResults?.[0]?.result || { error: "failed to execute API call on page context" };
        console.log("📥 [OBSCURA v6] Received API response:", apiResponse);

        // Step 4: Push the response back to the bridge
        await fetch(`${BRIDGE_URL}/push-generation-result`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(apiResponse)
        });

    } catch (e) {
        console.log("❌ [OBSCURA v6] In-browser generation failed:", e.message);
        await fetch(`${BRIDGE_URL}/push-generation-result`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ error: e.message || String(e) })
        });
    }
}
