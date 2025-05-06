from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <html>
    <head>
        <title>Telegram Bot Server</title>
        <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
    </head>
    <body>
        <div class="container mt-5">
            <div class="card">
                <div class="card-header">
                    <h3>O'quv Davomat Bot Server</h3>
                </div>
                <div class="card-body">
                    <h5 class="card-title">Bot holati</h5>
                    <p class="card-text">Telegram bot serveri ishlayapti. Iltimos, Telegram orqali botni ishlatishingiz mumkin.</p>
                    <hr>
                    <h5>Ma'lumot:</h5>
                    <ul>
                        <li><strong>Bot:</strong> Telegram ichida @oquv_davomat_bot (yoki manzilni botdan tekshiring)</li>
                        <li><strong>Buyruqlar:</strong>
                            <ul>
                                <li><code>/start</code> - botni boshlash va asosiy menyu</li>
                                <li><code>/davomat</code> - o'quvchining darsga kelganini belgilash</li>
                                <li><code>/royxat</code> - yangi o'quvchi ma'lumotlarini kiritish</li>
                                <li><code>/tolov</code> - to'lov ma'lumotlarini kiritish</li>
                                <li><code>/hisobot</code> - o'quvchilar bo'yicha hisobot olish</li>
                            </ul>
                        </li>
                    </ul>
                </div>
                <div class="card-footer text-muted">
                    Davomat ma'lumotlari Google Sheets'ga saqlanadi
                </div>
            </div>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
