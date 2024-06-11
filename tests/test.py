import asyncio
from halina.email_rapport.email_sender import EmailSender


async def main():
    context = {
        'message': 'To jest przykładowy mail z tabelą i zdjęciem.',
        'table_data': [
            ['Kolumna 1', 'Kolumna 2'],
            ['Wartość 1', 'Wartość 2'],
            ['Wartość 3', 'Wartość 4']
        ]
    }

    email_sender = EmailSender(
        to_email='d.chmalu@gmail.com',
        subject='Test Przykładowy mail z tabelą i zdjęciem',
        template_name='email_template.html',
        context=context,
        image_path='src/halina/email_rapport/zdjecie.png',
    )

    result = await email_sender.send()
    if result:
        print("Mail wysłany pomyślnie!")
    else:
        print("Wysyłka maila nie powiodła się.")

if __name__ == "__main__":
    asyncio.run(main())
