// Ugh, Morty, alright, let's get this over with. We're gonna create 3 tasks for every Contact in the org, okay? 
// Set the Subject to "Outbound Call" and default the rest of the required fields. 

List<Contact> contacts = [SELECT Id FROM Contact];
List<Task> tasksToInsert = new List<Task>();

for (Contact con : contacts) {
    for (Integer i = 0; i < 3; i++) {
        Task t = new Task();
        t.Subject = 'Outbound Call';
        t.WhoId = con.Id;
        t.Status = 'Not Started';
        t.Priority = 'Normal';
        tasksToInsert.add(t);
    }
}

insert tasksToInsert;
