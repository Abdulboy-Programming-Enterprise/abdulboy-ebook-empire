# User Management - Admin Guide

## User Management Overview

Access user management at `/admin/users-manager.html`

## User List

### Columns

| Column | Description |
|--------|-------------|
| Email | User's email address |
| Full Name | Display name |
| Account Type | admin, special, normal |
| Subscription Status | free, basic, premium |
| Joined | Registration date |
| Actions | Edit/Delete buttons |

### Filtering

| Filter | Options |
|--------|---------|
| User Type | All, Admin, Special, Normal |
| Subscription | All, Free, Basic, Premium |
| Status | Active, Suspended |

### Searching

- Search by email
- Search by name
- Partial matches supported

## Creating Users

### Regular User

1. Click "Add User"
2. Enter email, name, password
3. Select account type (Normal)
4. User receives welcome email

### Special User (VIP)

Special users get free access to all books:

1. Go to Special Accounts page
2. Click "Create Special User"
3. Enter email and name
4. User created with premium access

### Admin User

1. Go to Admin Accounts page
2. Click "Create Admin"
3. Enter email and name
4. Temporary password sent via email

## Editing Users

### Update Profile

1. Click "Edit" next to user
2. Modify fields:
   - Full name
   - Email
   - Account type
3. Save changes

### Reset Password

1. Click "Reset Password"
2. Confirm action
3. Temporary password emailed
4. User must change on next login

### Manage Subscription

1. View user's current plan
2. Upgrade/downgrade manually
3. Add trial period
4. Cancel subscription

## Suspending Users

### Temporary Suspension

- User cannot log in
- Account data preserved
- Can be reinstated

### Permanent Ban

- User permanently blocked
- Option to delete data (GDPR)
- Cannot be reversed

## Viewing User Details

### Available Information

- **Profile**: Name, email, avatar
- **Subscription**: Plan, start date, end date
- **Purchase History**: All transactions
- **Reading Activity**: Books read, time spent
- **Support Tickets**: Open/closed tickets
- **Audit Log**: Admin actions affecting user

## Special Account Management

### Creating Special Accounts

Special accounts have unlimited free access:

1. Navigate to Special Accounts
2. Click "Create Special User"
3. Enter user details
4. Account activated immediately

### Removing Special Privileges

1. Find user in special accounts list
2. Click "Remove Special"
3. User reverts to normal account
4. Subscription status updated

## Admin Account Management

### Creating Admins

1. Navigate to Admin Accounts
2. Click "Add Admin"
3. Enter email and name
4. Temporary password generated
5. Admin must change password on first login

### Removing Admin Privileges

1. Cannot remove your own admin
2. Select target admin
3. Click "Remove Admin"
4. User becomes normal user

## Audit Logs

### What's Logged

- User creation
- Role changes
- Subscription modifications
- Account suspension
- Password resets

### Viewing Logs

1. Go to Audit Logs section
2. Filter by user
3. Filter by action type
4. Export logs (CSV)

## GDPR Compliance

### Data Export

1. Find user
2. Click "Export Data"
3. Generate ZIP with all user data
4. Download link valid for 7 days

### Data Deletion

1. Request deletion (or admin initiated)
2. 30-day grace period
3. Permanent deletion after grace period
4. Confirmation email sent

## Bulk Operations

### Export Users

1. Apply filters
2. Click "Export"
3. Choose format (CSV, JSON)
4. Download file

### Bulk Update

1. Select multiple users
2. Choose action:
   - Change subscription
   - Send notification
   - Export data
3. Confirm action

## Notifications

### Send to Users

1. Select users (individual or bulk)
2. Compose message
3. Choose notification type (email, in-app)
4. Send

### Templates

- Welcome email
- Subscription reminder
- Account suspended
- Account deleted

## Best Practices

1. **Regular Audits**: Review admin accounts monthly
2. **Special Accounts**: Limit to legitimate VIPs
3. **Suspension**: Document reason for actions
4. **Data Privacy**: Handle user data carefully
5. **Support**: Respond to user reports promptly

## Troubleshooting

### User Can't Log In

- Check account status (not suspended)
- Verify email verification
- Reset password
- Check login attempts

### Subscription Not Active

- Verify payment status
- Check subscription dates
- Manual override available

### Special Access Not Working

- Confirm account type is "special"
- Check subscription end date
- Re-apply privileges
