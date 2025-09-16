def find_student(students):
    if not students:
        print("当前没有学生信息，请先录入学生信息。")
        return
    student_id = input("请输入要查找的学生学号: ").strip()
    if student_id in students:
        student = students[student_id]
        print(f"\n找到学生信息:\n学号: {student['学号']}\n姓名: {student['姓名']}\n性别: {student['性别']}\n宿舍房间号: {student['宿舍房间号']}\n联系电话: {student['联系电话']}")
    else:
        print(f"未找到学号为 {student_id} 的学生信息。")

def add_student(students):
    print("\n开始录入新学生信息")
    while True:
        student_id = input("请输入学号: ").strip()
        if not student_id:
            print("学号不能为空，请重新输入。")
            continue
        if student_id in students:
            print("该学号已存在，请重新输入。")
            continue
        break
    name = input("请输入姓名: ").strip()
    while not name:
        print("姓名不能为空，请重新输入。")
        name = input("请输入姓名: ").strip()
    gender = input("请输入性别(男/女): ").strip()
    while gender not in ['男', '女']:
        print("性别输入错误，请输入'男'或'女'。")
        gender = input("请输入性别(男/女): ").strip()
    room = input("请输入宿舍房间号: ").strip()
    while not room:
        print("宿舍房间号不能为空，请重新输入。")
        room = input("请输入宿舍房间号: ").strip()
    phone = input("请输入联系电话: ").strip()
    while not phone:
        print("联系电话不能为空，请重新输入。")
        phone = input("请输入联系电话: ").strip()
    print(f"\n请确认学生信息:\n学号: {student_id}\n姓名: {name}\n性别: {gender}\n宿舍房间号: {room}\n联系电话: {phone}")
    confirm = input("\n确认录入吗? (y/n): ").strip().lower()
    if confirm == 'y':
        students[student_id] = {
            '学号': student_id,
            '姓名': name,
            '性别': gender,
            '宿舍房间号': room,
            '联系电话': phone
        }
        print("学生信息录入成功!")
    else:
        print("已取消录入。")

def display_all_students(students):
    if not students:
        print("当前没有学生信息，请先录入学生信息。")
        return
    print(f"{'-' * 60}\n{'学号':<10} {'姓名':<8} {'性别':<4} {'宿舍房间号':<10} {'联系电话':<12}\n{'-' * 60}")
    for student_id, info in students.items():
        print(f"{info['学号']:<12} {info['姓名']:<8} {info['性别']:<4} {info['宿舍房间号']:<10} {info['联系电话']:<12}")
    print(f"{'-' * 60}\n总计: {len(students)} 名学生")

def save_data(students, filename="dormitory_data.txt"):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for student_id, info in students.items():
                f.write(f"{info['学号']},{info['姓名']},{info['性别']},{info['宿舍房间号']},{info['联系电话']}\n")
        print(f"数据已保存到 {filename}")
    except Exception as e:
        print(f"保存数据时出错: {e}")

def load_data(filename="dormitory_data.txt"):
    students = {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                data = line.strip().split(',')
                if len(data) == 5:
                    student_id, name, gender, room, phone = data
                    students[student_id] = {
                        '学号': student_id,
                        '姓名': name,
                        '性别': gender,
                        '宿舍房间号': room,
                        '联系电话': phone
                    }
        print(f"已从 {filename} 加载数据")
    except FileNotFoundError:
        with open(filename, 'w', encoding='utf-8') as f:
                pass  # 只是创建文件，不写入内容
        print("未找到数据文件，将创建新文件。")
    except Exception as e:
        print(f"加载数据时出错: {e}")
    return students

print("欢迎使用学生宿舍管理系统!")
students = load_data()
print("=" * 40 + "\n        学生宿舍管理系统\n" + "=" * 40 + "\n1. 查找学生信息\n2. 录入新学生信息\n3. 显示所有学生信息\n4. 退出系统\n" + "=" * 40)
while True:
    choice = input("请选择操作 (1-4): ").strip()
    if choice == '1':
        find_student(students)
    elif choice == '2':
        add_student(students)
    elif choice == '3':
        display_all_students(students)
    elif choice == '4':
        save_data(students)
        print("感谢使用学生宿舍管理系统，再见!")
        break
    else:
        print("无效选择，请重新输入。")
    input("\n按回车键继续...")
