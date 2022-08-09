import os

style = os.environ.get('INTEGRATION_STYLE')
if style and style.lower() == "server_to_server":
  from app.server_to_server import app
  if __name__ == "__main__":
    app.run()
else:
  from app.browser_initiated import app
  if __name__ == "__main__":
    app.run()