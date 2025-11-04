from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta

app = Flask(__name__)

# =========================
# 🔁 Circular Queue Class
# =========================
class CircularQueue:
    def __init__(self, size):
        self.size = size
        self.queue = [None] * size
        self.front = self.rear = -1

    def enqueue(self, data):
        if (self.rear + 1) % self.size == self.front:
            # Queue full → overwrite oldest
            self.front = (self.front + 1) % self.size
        if self.front == -1:
            self.front = 0
        self.rear = (self.rear + 1) % self.size
        self.queue[self.rear] = data

    def get_all(self):
        if self.front == -1:
            return []
        result = []
        i = self.front
        while True:
            result.append(self.queue[i])
            if i == self.rear:
                break
            i = (i + 1) % self.size
        return result

    def clear(self):
        self.front = self.rear = -1
        self.queue = [None] * self.size


# =========================
# 🧩 Hash Table for User Activity
# =========================
class HashTable:
    def __init__(self):
        self.table = {}

    def add_log(self, user, timestamp, action):
        self.table.setdefault(user, []).append((timestamp, action))

    def get_top_users(self):
        # Sort by descending number of actions
        users = [(user, len(actions)) for user, actions in self.table.items()]
        return sorted(users, key=lambda x: x[1], reverse=True)

    def get_suspicious_users(self):
        suspicious = []
        for user, actions in self.table.items():
            times = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts, _ in actions]
            times.sort()
            for i in range(len(times)):
                count = 1
                for j in range(i + 1, len(times)):
                    if (times[j] - times[i]) <= timedelta(minutes=1):
                        count += 1
                    else:
                        break
                # ⚠️ ≥10 actions in 1 minute
                if count >= 10:
                    suspicious.append((user, count))
                    break
        return suspicious

    def clear(self):
        self.table.clear()


# =========================
# 🌐 Flask Routes
# =========================
queue = CircularQueue(1000)
user_logs = HashTable()

@app.route('/')
def home():
    logs = queue.get_all()
    return render_template('index.html', logs=logs)

@app.route('/add', methods=['POST'])
def add_log():
    user = request.form['user']
    action = request.form['action']
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Live time

    log_entry = {"user": user, "timestamp": timestamp, "action": action}
    queue.enqueue(log_entry)
    user_logs.add_log(user, timestamp, action)

    return redirect(url_for('home'))

@app.route('/top')
def top_users():
    top = user_logs.get_top_users()
    return render_template('result.html', title="📊 Top Active Users (Descending)", results=top)

@app.route('/suspicious')
def suspicious_users():
    sus = user_logs.get_suspicious_users()
    return render_template('result.html', title="⚠️ Suspicious Users (≥10 actions/min)", results=sus)

@app.route('/clear')
def clear_logs():
    global queue, user_logs
    queue.clear()
    user_logs.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
