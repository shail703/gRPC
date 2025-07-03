# Distributed gRPC-based Learning-Management System  
## (Raft + gRPC Project — Milestone 3)


Milestone 3 brings the whole project together: a **fault-tolerant Learning-Management
System (LMS)** that replicates state across multiple nodes with the Raft consensus
algorithm, exposes a rich gRPC API to clients, synchronises files automatically,
and even embeds an optional lightweight LLM server for natural-language Q&A over
course material.

---

## ✨  Highlights

| Area | What’s new in M-3 |
|------|------------------|
| **Consensus** | Full Raft election/heartbeat cycle (`FOLLOWER → CANDIDATE → LEADER`). |
| **State replication** | JSON data + assignment/content folders replicated from the leader to followers via REST helpers (`leader_sync.py` ↔ `receiver_server.py`). |
| **LMS gRPC service** | Complete CRUD for users / assignments / submissions / doubts plus file-transfer RPCs, defined in `lms.proto`. |
| **LLM micro-service** | Optional `LLMserver.py` answers student questions using local files, teaching prompts or a fallback GPT-2 model. |
| **Client CLI** | `client.py` interactive menu for students & teachers. |
| **Hot-reload logging** | File-system events are streamed to a log and trigger leader→follower sync automatically (`watchdog` observers). |

---

## 🏛️  Architectural Overview

```text
┌────────────┐      heartbeat/vote_req      ┌────────────┐
│  Node A    │◀────────────────────────────▶│  Node B    │
│ (Leader)   │                             │ (Follower) │
└────────────┘                             └────────────┘
        ▲                                        ▲
        │  file sync (Flask)                     │
        ▼                                        ▼
┌─────────────────────────────────────────────────────────┐
│  assignments/  content/  *.json          (shared data) │
└─────────────────────────────────────────────────────────┘
        ▲
        │  gRPC  (LMS + LLM)
        ▼
┌─────────────────────────────────────────────────────────┐
│               Client CLI  (student / teacher)          │
└─────────────────────────────────────────────────────────┘
```

*   **Raft layer (`node.py`, `server.py`)** keeps every node’s state machine in sync.  
*   **gRPC layer (`server_script.py`)** hosts two services:  
    * `LMS` – user management, assignments, grading, doubts.  
    * `LLMService` – optional Q&A endpoint.  
*   **File-sync helpers** copy PDFs, text content and JSON databases from the
    current leader to all followers whenever changes are observed.

---

## 🗂️  Repository Layout

| Path | Purpose |
|------|---------|
| `node.py` | Core Raft logic (timeouts, elections, heartbeat). |
| `server.py` | Boot-straps a Raft node and a lightweight Flask façade. |
| `server_script.py` | Hosts the gRPC LMS + LLM services and filesystem watcher. |
| `LLMserver.py` | Stand-alone LLM micro-service (optional). |
| `lms.proto` | gRPC service definitions (compile with `python -m grpc_tools.protoc ...`). |
| `leader_sync.py` / `receiver_server.py` | Leader-driven file replication endpoints. |
| `client.py` | Interactive CLI for students/teachers. |
| `assignments/`, `content/` | Persisted course artefacts. |
| `ip_list.txt` | One URL per node, used by `server.py` at startup. |

---

## ⚙️  Prerequisites

* Python 3.9+
* `pip install grpcio grpcio-tools flask watchdog requests sentence-transformers transformers torch protobuf`
* (Optional) CUDA-enabled GPU for faster LLM inference.

---

## 🔧  Setup & Run

### 1. Clone & Install

```bash
git clone https://github.com/shail703/gRPC -b milestone-3
cd gRPC
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # or use the list above
```

### 2. Configure cluster IPs

Edit **`ip_list.txt`** so each line contains  
`http://<host>:<port>` for every node in the cluster.  
The **index** of a line is the positional argument you pass to `server.py`.

### 3. Launch Raft nodes (one per machine / terminal)

```bash
# On node-0
python server.py 0 ip_list.txt

# On node-1
python server.py 1 ip_list.txt
# …and so on
```

### 4. Start the LLM service (optional)

```bash
python LLMserver.py
```

### 5. Use the CLI

```bash
python client.py
```

The CLI discovers the leader automatically (redirection handled in `server.py`) and
offers separate menus for **students** and **teachers**.

---

## 🛰️  gRPC API (excerpt)

```proto
service LMS {
  rpc RegisterStudent  (RegisterRequest)  returns (RegisterResponse);
  rpc Login            (LoginRequest)     returns (LoginResponse);
  rpc Get              (GetRequest)       returns (GetResponse);   // view_* ops
  rpc Post             (PostRequest)      returns (PostResponse);  // submit/grade
  rpc UploadFile       (UploadFileRequest) returns (UploadFileResponse);
  rpc DownloadFile     (DownloadFileRequest) returns (DownloadFileResponse);
  rpc ViewSubmission   (ViewSubmissionRequest) returns (ViewSubmissionResponse);
  rpc ViewQuestions    (ViewQuestionsRequest) returns (ViewQuestionsResponse);
}

service LLMService {
  rpc getLLMAnswer (LLMQueryRequest) returns (LLMQueryResponse);
}
```

See **`lms.proto`** for all messages and optional fields.

---

## 🧪  Quick smoke-test

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. lms.proto
python test.py   # Sends a dummy LLM query on localhost:50055
```

---

## 🚨  Security & Secrets

An **OpenAI key is hard-coded in `test.py`; remove it before committing
publicly.**  
Consider moving all secrets to environment variables and adding a
`requirements.txt`/`.env.example` in a future milestone.

---

## 📄  License

⚠️ No licence file yet – contributions default to **All Rights Reserved**.  
Add an OSS licence (MIT, Apache-2.0, etc.) if you intend to open-source.

---

*Milestone 3 completed – the system now functions end-to-end with high
availability, consistent state, and an enriched learning experience.*
