# splite3をimportする
import sqlite3
# flaskをimportしてflaskを使えるようにする
from flask import Flask, render_template, request, redirect, session

# appにFlaskを定義して使えるようにしています。Flask クラスのインスタンスを作って、 app という変数に代入しています。
app = Flask(__name__)

# Flask では標準で Flask.secret_key を設定すると、sessionを使うことができます。この時、Flask では session の内容を署名付きで Cookie に保存します。
app.secret_key = 'mbaco'


@app.route('/')
def top():
    return render_template('top.html')


# GET  /register => 登録画面を表示
# POST /register => 登録処理をする
@app.route('/index', methods=["GET", "POST"])
def index():
    #  登録ページを表示させる
    if request.method == "GET":
        if 'user_id' in session:
            return redirect('/mypage')
        else:
            return render_template("index.html")
    # ここからPOSTの処理
    else:
        name = request.form.get("name")
        password = request.form.get("password")
        email = request.form.get("email")

        conn = sqlite3.connect('mama_refre1.db')
        c = conn.cursor()
        c.execute("insert into user values(null,?,?,?)",
                  (name, email, password))
        conn.commit()
        conn.close()
        return redirect('/login')


# GET  /login => ログイン画面を表示
# POST /login => ログイン処理をする
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if 'user_id' in session:
            return redirect("/mypage")
        else:
            return render_template("login.html")
    else:
        # ブラウザから送られてきたデータを受け取る
        email = request.form.get("email")
        password = request.form.get("password")

        # ブラウザから送られてきた name ,password を userテーブルに一致するレコードが
        # 存在するかを判定する。レコードが存在するとuser_idに整数が代入、存在しなければ nullが入る
        conn = sqlite3.connect('mama_refre1.db')
        c = conn.cursor()
        c.execute(
            "select user_id from user where email = ? and password = ?", (email, password))
        user_id = c.fetchone()
        conn.close()

        # user_id が NULL(PythonではNone)じゃなければログイン成功
        if user_id is None:
            # ログイン失敗すると、ログイン画面に戻す
            return render_template("login.html")
        else:
            session['user_id'] = user_id[0]
            return redirect("/mypage")


@app.route("/mypage", methods=["GET", "POST"])
def mypage():
    if request.method == "GET":
        if 'user_id' in session:
            id = session['user_id']
            conn = sqlite3.connect('mama_refre1.db')
            c = conn.cursor()
            c.execute(
                "select fac_name,date,time from past_log join facility on past_log.fac_id = facility.fac_id where user_id=?", (id,))
            pastlist = c.fetchall()
            c.execute(
                "select fac_name,date,time from entry join facility on entry.fac_id = facility.fac_id where user_id=?", (id,))
            entrylist = c.fetchall()
            conn.close()
            return render_template("mypage.html", pastlist=pastlist, entrylist=entrylist)
        else:
            return render_template("login.html")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop('user_id', None)
    # ログアウト後はログインページにリダイレクトさせる
    return redirect("/login")


@app.route('/review')
def review():
    if 'user_id' in session:
        # クッキーからuser_idを取得
        user_id = session['user_id']
        conn = sqlite3.connect('mama_refre1.db')
        c = conn.cursor()
        # # DBにアクセスしてログインしているユーザ名と投稿内容を取得する
        # クッキーから取得したuser_idを使用してuserテーブルのnameを取得
        c.execute("select name from user where user_id = ?", (user_id,))
        # fetchoneはタプル型
        user_info = c.fetchone()
        c.execute(
            "select user_id,name from user where user_id = ? order by user_id", (user_id,))
        comment_list = []
        for row in c.fetchall():
            comment_list.append({"id": row[0], "comment": row[1]})

        c.close()
        return render_template('review.html', user_info=user_info, comment_list=comment_list)
    else:
        return redirect("/login")


@app.route('/add', methods=["POST"])
def add():
    user_id = session['user_id']
    # フォームから入力されたアイテム名の取得
    comment = request.form.get("comment")
    conn = sqlite3.connect('service.db')
    c = conn.cursor()
    # DBにデータを追加する
    c.execute("insert into bbs values(null,?,?)", (user_id, comment))
    conn.commit()
    conn.close()
    return redirect('/review')


@app.route('/edit/<int:id>')
def edit(id):
    if 'user_id' in session:
        conn = sqlite3.connect('service.db')
        c = conn.cursor()
        c.execute("select comment from bbs where id = ?", (id,))
        comment = c.fetchone()
        conn.close()

        if comment is not None:
            # None に対しては インデクス指定できないので None 判定した後にインデックスを指定
            comment = comment[0]
            # "りんご" ○   ("りんご",) ☓
            # fetchone()で取り出したtupleに 0 を指定することで テキストだけをとりだす
        else:
            return "アイテムがありません"  # 指定したIDの name がなければときの対処

        item = {"id": id, "comment": comment}

        return render_template("edit.html", comment=item)
    else:
        return redirect("/login")


# /add ではPOSTを使ったので /edit ではあえてGETを使う
@app.route("/edit")
def update_item():
    if 'user_id' in session:
        # ブラウザから送られてきたデータを取得
        item_id = request.args.get("item_id")  # id
        item_id = int(item_id)  # ブラウザから送られてきたのは文字列なので整数に変換する
        comment = request.args.get("comment")  # 編集されたテキストを取得する

        # 既にあるデータベースのデータを送られてきたデータに更新
        conn = sqlite3.connect('service.db')
        c = conn.cursor()
        c.execute("update bbs set comment = ? where id = ?",
                  (comment, item_id))
        conn.commit()
        conn.close()

        # アイテム一覧へリダイレクトさせる
        return redirect("/review")
    else:
        return redirect("/login")


@app.route('/del', methods=["POST"])
def del_task():
    # クッキーから user_id を取得
    id = request.form.get("comment_id")
    id = int(id)
    conn = sqlite3.connect("service.db")
    c = conn.cursor()
    c.execute("delete from bbs where id = ?", (id,))
    conn.commit()
    c.close()
    return redirect("/bbs")


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/golf')
def golf():
    return render_template('golf.html')


@app.errorhandler(403)
def mistake403(code):
    return 'urlが間違っています'


@app.errorhandler(404)
def notfound404(code):
    return "お探しのページは見つかりません"


# __name__ というのは、自動的に定義される変数で、現在のファイル(モジュール)名が入ります。 ファイルをスクリプトとして直接実行した場合、 __name__ は __main__ になります。
if __name__ == "__main__":
    # Flask が持っている開発用サーバーを、実行します。
    app.run(host="localhost", port=5000, debug=True)
