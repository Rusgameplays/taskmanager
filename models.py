from data import save_tasks

def add_task(tasks):
    new = {
        "id": "RF",
        "name": "АС",
        "type": "",
        "mp8":"",
        "secure": "Не задан",
        "status": "В работе",
        "full_name": "",
        "second_id": "SD",
        "pentest/audit": "",
        "compliance": "",
        "comment": ""
    }
    tasks.append(new)
    save_tasks(tasks)


def delete_task(tasks, index):
    del tasks[index]
    save_tasks(tasks)


def set_status(tasks, index, status):
    tasks[index]["status"] = status
    save_tasks(tasks)


def auto_fill_from_system(tasks, task):
    for t in tasks:
        if t is task:
            continue

        if t["name"].strip().lower() == task["name"].strip().lower():
            task["secure"] = t.get("secure", "")
            task["full_name"] = t.get("full_name", "")
            break

    save_tasks(tasks)