// Create 10 Accounts

Id userId = '005DJ000005jiUIYAY';
List<Account> accounts = new List<Account>();
Datetime now = Datetime.now();
for (Integer i = 0; i < 10; i++) {
    accounts.add(new Account(Name = 'Account ' + now.format('yyyy-MM-dd HH:mm:ss') + ' ' + i, OwnerId=userId));
}
insert accounts;

// Create 2 Contacts per Account
List<Contact> contacts = new List<Contact>();
for (Account acc : accounts) {
    for (Integer i = 0; i < 2; i++) {
        contacts.add(new Contact(
            AccountId = acc.Id,
            LastName = 'Contact ' + i + ' for ' + acc.Name
        ));
    }
}
insert contacts;

// Create 3 Tasks per Contact with required fields
List<Task> tasks = new List<Task>();
for (Contact con : contacts) {
    for (Integer i = 0; i < 3; i++) {
        // String subject = i == 0 ? 'Call Connect' : i == 1 ? 'Dial' : i == 2 ? 'Outbound Email' : 'Other';
        String subject = 'Outbound Email';
        tasks.add(new Task(
            WhoId = con.Id,
            Subject = subject,
            OwnerId=userId,
            ActivityDate = Date.today().addDays(i),
            Status = 'Not Started',
            // Type = subject == 'Other' ? 'Email' : null,
            Priority = 'Normal'
        ));
    }
}
insert tasks;

System.debug('Created ' + accounts.size() + ' Accounts');
System.debug('Created ' + contacts.size() + ' Contacts');
System.debug('Created ' + tasks.size() + ' Tasks');
