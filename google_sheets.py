import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import config

# Налаштування Google Sheets
def setup_google_sheets():
    if not config.GOOGLE_SHEETS_ENABLED:
        return None
    
    try:
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        
        creds = Credentials.from_service_account_file(
            config.GOOGLE_CREDENTIALS_FILE, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(config.GOOGLE_SHEET_ID).sheet1
        return sheet
    except Exception as e:
        print(f"Помилка підключення до Google Sheets: {e}")
        return None

# Додавання користувача в таблицю
def add_user_to_sheet(user_id, first_name, username, phone):
    if not config.GOOGLE_SHEETS_ENABLED:
        return
    
    try:
        sheet = setup_google_sheets()
        if sheet:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Колонки: A=User ID, B=First Name, C=Username, D=Phone, E=Date
            row = [str(user_id), first_name, username or "", phone, current_time]
            sheet.append_row(row)
            print(f"Користувач {first_name} додан в Google Sheets")
    except Exception as e:
        print(f"Помилка додавання в Google Sheets: {e}")

# ВИПРАВЛЕНО: функція тепер автоматично генерує timestamp
def add_quiz_result(user_id, score):
    if not config.GOOGLE_SHEETS_ENABLED:
        return
    
    try:
        sheet = setup_google_sheets()
        if sheet:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Знаходимо користувача та додаємо результат
            all_values = sheet.get_all_values()
            for i, row in enumerate(all_values):
                if len(row) > 0 and str(row[0]) == str(user_id):
                    # Додаємо результат в колонку F (Quiz Score) і G (Quiz Date)
                    sheet.update(f'F{i+1}', score)
                    sheet.update(f'G{i+1}', current_time)
                    print(f"Результат {score} додан для користувача {user_id}")
                    return
            
            # Якщо користувача не знайдено, виводимо повідомлення
            print(f"Користувач {user_id} не знайдений в таблиці для збереження результату")
            
    except Exception as e:
        print(f"Помилка збереження результату в Google Sheets: {e}")

def mark_academy_interest(user_id):
    """Додає позначку 'цікаво' в колонку H і '1' в колонку I для користувача, який зацікавився академією"""
    if not config.GOOGLE_SHEETS_ENABLED:
        return
    
    try:
        sheet = setup_google_sheets()
        if sheet:
            # Знаходимо користувача та додаємо позначку
            all_values = sheet.get_all_values()
            user_found = False
            
            for i, row in enumerate(all_values):
                if len(row) > 0 and str(row[0]) == str(user_id):
                    row_number = i + 1
                    
                    try:
                        # Додаємо текст "цікаво" в колонку H
                        sheet.update_cell(row_number, 8, 'цікаво')  # 8 = колонка H
                        
                        # Додаємо "1" в колонку I для підрахунку
                        sheet.update_cell(row_number, 9, 1)  # 9 = колонка I
                        
                        # Додаємо зелене зафарбовування для колонки H
                        sheet.format(f'H{row_number}', {
                            "backgroundColor": {
                                "red": 0.8,
                                "green": 1.0,
                                "blue": 0.8
                            },
                            "textFormat": {
                                "bold": True,
                                "foregroundColor": {
                                    "red": 0.0,
                                    "green": 0.6,
                                    "blue": 0.0
                                }
                            }
                        })
                        
                        print(f"Позначка 'цікаво' та '1' додані для користувача {user_id}")
                        user_found = True
                        break
                        
                    except Exception as format_error:
                        print(f"Помилка форматування: {format_error}")
                        try:
                            sheet.update_cell(row_number, 8, 'цікаво')
                            sheet.update_cell(row_number, 9, 1)
                            print(f"Позначка 'цікаво' та '1' додані для користувача {user_id} (без форматування)")
                            user_found = True
                            break
                        except Exception as text_error:
                            print(f"Помилка додавання тексту: {text_error}")
            
            if not user_found:
                print(f"Користувач {user_id} не знайдений в таблиці для позначки академії")
                
    except Exception as e:
        print(f"Помилка позначки академії в Google Sheets: {e}")
        import traceback
        traceback.print_exc()

# Додаткова функція для перевірки структури таблиці
def check_sheet_structure():
    """Перевіряє та створює заголовки колонок, якщо їх немає"""
    if not config.GOOGLE_SHEETS_ENABLED:
        return
    
    try:
        sheet = setup_google_sheets()
        if sheet:
            # Перевіряємо перший рядок (заголовки)
            headers = sheet.row_values(1)
            expected_headers = ['User ID', 'First Name', 'Username', 'Phone', 'Date', 'Quiz Score', 'Quiz Date', 'Academy Interest', 'Count']
            
            if not headers or len(headers) < len(expected_headers):
                print("Додаю заголовки до таблиці...")
                sheet.insert_row(expected_headers, 1)
                print("Заголовки додано успішно!")
            else:
                print("Структура таблиці коректна")
                
    except Exception as e:
        print(f"Помилка перевірки структури таблиці: {e}")