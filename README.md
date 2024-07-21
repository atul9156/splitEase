# SplitEase

SplitEase is a web application designed to simplify the process of splitting expenses and managing group finances. It helps users track shared expenses within a group and calculates the most efficient way to settle debts among group members.

## Features

- **Group Management**: Create and manage groups for shared expenses.
- **Expense Tracking**: Add, edit, and delete expenses within a group.
- **Balance Calculation**: Automatically calculates each member's balance based on their contributions and shared expenses.
- **Optimal Settlement**: Determines the most efficient way to settle debts within the group.
- **User-friendly Interface**: An intuitive and user-friendly interface for easy navigation.

### User stories

1. Groups
    - Creating Groups
        - As a user, I want to create new groups so that I can organize my expenses with my friends.
        - As a user, I want to specify the group members when creating a group, allowing me to add initial group members.

    - Managing Group Members
        - As a group member, I want to add other users to the group, enabling us to share expenses.
        - As a group member, I want to remove users from the group when needed.
        - As a group member, I want to delete the group if it's no longer required.

    - Group Permissions
        - As a group member, I want to have permission to:
            - Add other members to the group.
            - Remove other members from the group.
            - Delete the group.
            - Add transactions to the group.

2. Balances
    - Viewing Balances
        - As a group member, I want to view the individual balances for each user within the group.
        - As a group member, I want to see a clear summary of who owes whom and the corresponding amounts.
        - As a group member, I want a simplified view of the balances to understand the overall financial situation within the group.

3. Transactions
    - Adding Transactions
        - As a group member, I want to add transactions to a group, specifying details such as:
            - Flexible payment proportions, allowing any number of users to pay in any ratio.
            - Splitting a bill between any number of users in any proportion.
            - Splitting transactions by share, percentage, or specific amounts owed by each person.

    - Managing Transactions
        - As a group member, I want to update transaction details when necessary, ensuring accuracy.
        - As a group member, I want the ability to delete transactions if they were added in error or are no longer relevant.

## Getting Started

To run SplitEase locally on your machine, follow these steps:

### Prerequisites

- Python 3.x
- Django
- Django REST framework
- SQLite or your preferred database system

### Installation

1. Create a virtual environment for this project. Make sure to use python 3.8 for best experience (this version was used for development). You can use either of [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) or [venv](https://python.land/virtual-environments/virtualenv) to create and manage the virtual environment

2. To install the required dependencies, run the below command

    ```bash
    pip install -r requirements.txt
    ```

3. Run the below command to create migrations

    ```bash
    python manage.py migrate
    ```

4. Run the below command to start the django server on port 8000

    ```bash
    python manage.py runserver
    ```

**Note:** Steps 2-4 should be carried out inside the project directory (in the directory which has manage.py)

## Working with examples

Below are the steps one needs to follow to simulate exampe 1 of the assignment:

1. Create one user. This step registers the user with the app

    ```bash
    curl --location 'http://localhost:8000/users/' \
    --header 'Content-Type: application/json' \
    --data-raw '{
    "name": "Harry",
    "email": "harry@example.com"
    }'
    ```

2. Create a group. For the sake of demonstration, we will create a group by the anem `Sample 1`

    ```bash
    curl --location 'http://localhost:8000/groups/' \
    --header 'User-Email: harry@example.com' \
    --header 'Content-Type: application/json' \
    --data '{
        "name": "Sample 1"
    }'
    ```

3. Add transactions to the group. Below is the sample of how a transaction of `$200` by the name `Museum  Ticket`, paid by `harry` and split between the other users `harry`, `isla`, `jack`, `kate` and `lily` equally.

    ```bash
    curl --location 'http://localhost:8000/groups/1/add_transaction/' \
    --header 'Content-Type: application/json' \
    --header 'User-Email: harry@example.com' \
    --data-raw '{
        "name": "Museum Ticket",
        "amount": 200,
        "paid_by": {
            "users": ["harry@example.com"],
            "share": [100],
            "type": "percentage"
        },
        "shared_by": {
            "users": ["harry@example.com", "isla@example.com", "jack@example.com", "kate@example.com", "lily@example.com"],
            "share": [20, 20, 20, 20, 20],
            "type": "percentage"
        }
    }'
    ```

4. Use the below curls to add the remaining transactions

    ```bash
    # Lunch
    curl --location 'http://localhost:8000/groups/1/add_transaction/' \
    --header 'Content-Type: application/json' \
    --header 'User-Email: harry@example.com' \
    --data-raw '{
        "name": "Lunch",
        "amount": 120,
        "paid_by": {
            "users": ["isla@example.com"],
            "share": [100],
            "type": "percentage"
        },
        "shared_by": {
            "users": ["harry@example.com", "isla@example.com", "jack@example.com", "kate@example.com", "lily@example.com"],
            "share": [1, 2, 1, 1, 1],
            "type": "share"
        }
    }'

    # Coffee
    curl --location 'http://localhost:8000/groups/1/add_transaction/' \
    --header 'Content-Type: application/json' \
    --header 'User-Email: harry@example.com' \
    --data-raw '{
        "name": "Coffee",
        "amount": 80,
        "paid_by": {
            "users": ["jack@example.com"],
            "share": [100],
            "type": "percentage"
        },
        "shared_by": {
            "users": ["harry@example.com", "isla@example.com", "jack@example.com", "kate@example.com", "lily@example.com"],
            "share": [10, 20, 15, 15, 20],
            "type": "amount"
        }
    }'
    ```

5. Use the below curl to get the balance of each individual in the group

    ```bash
    curl --location 'http://localhost:8000/groups/1/list_balances' \
    --header 'User-Email: harry@example.com'
    ```

6. Use the below curl to get the optimal transaction for the group

    ```bash
    curl --location 'http://localhost:8000/groups/1/calculate_settlement/' \
    --header 'User-Email: harry@example.com'
    ```

***Note:*** There is a postman collection `API_Collection.postman_collection.json` which can be used to simulate all the above mentioned APIs and more for this project.

## Design decisions and some nuances

1. **Authorisation and Authentication**: Authorisation and authentication is implemented by adding an extra field `User-Email` in the request headers. This is a hacky way to implement authorisation and is only used for fast implementation of the project. For a fully functional production setup, JWT or OAuth based authorisation and authentication should be impemented. Authorisation is implemented on all APIs that work with the following resources
    - Groups
    - Transactions

    The authorisation is implemented for serving the below usecases
    - A user who is not part of the group (henceforth `rogue user`) should not be able to perform any operation of a group like
        - view the tranactionsvk
        - view group members
        - view balances
        - add/modify/delete transaction
        - modify membership of the group members

    **Rationale**: Quick implementaion

2. **Relation between the resources**: There are three resources for this proejct - `User`, `Group` and `Transaction`. By design
    - a `User` can exist independent of the group
    - A `Group` needs to have atleast 1 `User`. We cannot have a group with no `User`.
        - All group APIs require information of the user who is invoking the APIs.
        - When the group is being created for the first time, this user will be made part of the group automatically. Similarly, when the users are leaving group one by one as soon as the last person leaves the group, the group will be marked deleted
    - `Transaction` is always scoped to group(s). A transaction cannot exist outside of a group.

    **Rationale**: Seeing the examples it looked the expenses will always be preceeded by group creation

3. **On deletion**: All the resources (`User`, `Group`, `Transaction`) come with an implementation of soft-delete. The entries can be delete from the DB tables manually from the backend

    **Ratioanle**: Depending on the specific usecase, the geography in which the application is planning to operate, the local laws the firm with ownership of the app might want to retain the data (legally, of course) and process it later for other usecases (tagging transactions, generating user spending insights, selling loans to users based on spends etc)

4. **Duplicate groups**: There is no uniqueness contraint on the groups. Thi implies that users can create multiple groups with the same name.

    **Rationale**: Bill splitting apps like Splitwise also suffer from the same problem and they are yet to implement any solution. The problem of users creating multiple groups does not seem very plausible and certainly not one worth solving. But if it is absolutely necessary to handle this problem, then one can put a check while adding users in a group to see if they are part of any group with the same name. This can be implemented using [Django Signals](https://docs.djangoproject.com/en/5.0/ref/signals/), if necessary.
