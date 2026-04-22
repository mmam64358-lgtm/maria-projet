# projet-memoire

## Installation et exécution du projet

Suivez ces étapes pour installer et exécuter le projet sur votre machine :

### 1. Cloner le dépôt
```bash
git clone https://github.com/mmam64358-lgtm/projet-memoire.git
cd projet-memoire
```

### 2. Créer et activer un environnement virtuel (Windows)
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Lancer l'application
```bash
python app.py
```

---

**Remarques :**
- Si le projet nécessite des fichiers de configuration (ex: `.env`), veuillez les créer et les remplir selon les instructions du projet.
- Pour d'autres systèmes (Linux/Mac), l'activation de l'environnement virtuel se fait avec :
	```bash
	source .venv/bin/activate
	```
- Consultez le fichier `README.md` pour plus d'informations si besoin.

# كيفية تشغيل المشروع خطوة بخطوة

1. **تثبيت بايثون (Python)**
   - يجب أن يكون Python 3.10 أو أحدث مثبت على جهازك.

2. **فتح التيرمينال في مجلد المشروع**
   - مثال: إذا كان المشروع في مجلد التنزيلات (Downloads):
     
     افتح PowerShell أو CMD واكتب:
     
     """
     cd "C:\Users\hamza zourkane\Downloads\projet-memoire-main\projet-memoire-main"
     """

3. **إنشاء وتفعيل البيئة الافتراضية (مرة واحدة فقط)**
   - إنشاء البيئة:
     
     """
     python -m venv .venv
     """
   - تفعيل البيئة:
     - على PowerShell:
       """
       .venv\Scripts\Activate.ps1
       """
     - على CMD:
       """
       .venv\Scripts\activate.bat
       """
     - على Linux/macOS:
       """
       source .venv/bin/activate
       """

4. **تثبيت جميع المكتبات المطلوبة**
   - بعد تفعيل البيئة، ثبت المكتبات:
     
     """
     pip install -r requirements.txt
     """

5. **تشغيل البرنامج**
   - بعد تثبيت المكتبات، شغل التطبيق:
     
     """
     python app.py
     """

---

**ملاحظات مهمة:**
- يجب تفعيل البيئة الافتراضية كل مرة تفتح فيها التيرمينال قبل تشغيل البرنامج.
- إذا ظهرت رسالة خطأ عن مكتبة ناقصة، ثبتها بـ pip install اسم_المكتبة.
- إذا واجهت أي مشكل، انسخ رسالة الخطأ وأرسلها للمطور.