from app import create_app

app = create_app()
print("[INFO] Flask 应用初始化完成")

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)