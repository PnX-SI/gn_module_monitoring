def destination_name(module_name: str):
    return f"Monitoring - {module_name}"


def ask_confirmation(
    prompt="Veuillez confirmer que vous souhaitez effectuer avec ces modifications ? [yes/no]: ",
):

    response = input("\n" + prompt).strip().lower()

    while response not in ["yes", "y", "no", "n"]:
        print("Réponse invalide. Veuillez répondre par 'yes' ou 'no'.")
        response = input(prompt).strip().lower()

    return response in ["yes", "y"]
