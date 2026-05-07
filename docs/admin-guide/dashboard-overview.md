# Admin Dashboard - Overview

## Accessing the Dashboard

1. Log in with admin credentials
2. Navigate to `/admin/dashboard.html`
3. You'll see the main dashboard

## Dashboard Sections

### Statistics Cards

| Card | Description |
|------|-------------|
| Total Users | Number of registered users |
| New Users Today | Registrations in last 24h |
| Active Subscriptions | Current paying subscribers |
| Total Books | Books in catalog |
| Revenue (Total) | Lifetime revenue |
| Revenue (Monthly) | Current month revenue |
| Pending Payments | Unprocessed payments |
| Pending Bookings | Custom book requests |

### Charts

- **Revenue Chart**: Daily/weekly/monthly revenue trends
- **User Growth Chart**: New user registrations over time
- **Book Stats Chart**: Distribution by status/category

### Quick Actions

| Action | Description |
|--------|-------------|
| Add New Book | Open book creation form |
| Create Special User | Grant free access to user |
| Backup Database | Create manual backup |
| View Reports | Generate analytics reports |

## Navigation Menu

| Menu Item | Path | Description |
|-----------|------|-------------|
| Dashboard | `/admin/dashboard.html` | Main overview |
| Books | `/admin/books-manager.html` | Manage book catalog |
| Users | `/admin/users-manager.html` | Manage user accounts |
| Bookings | `/admin/bookings-manager.html` | Custom book requests |
| Payments | `/admin/payments-view.html` | Transaction history |
| Analytics | `/admin/analytics-view.html` | Detailed analytics |
| Special Users | `/admin/special-accounts.html` | VIP user management |
| Admins | `/admin/admin-accounts.html` | Admin account management |
| Reports | `/admin/reports.html` | Export data |
| Chatbot | `/admin/chatbot-training.html` | Train AI assistant |
| Backup | `/admin/backup-restore.html` | Backup management |
| Settings | `/admin/settings.html` | System configuration |

## User Roles

| Role | Permissions |
|------|-------------|
| Admin | Full access to all features |
| Special User | Free access to all books |
| Normal User | Regular user privileges |

## Best Practices

1. **Regular Monitoring**: Check dashboard daily
2. **User Management**: Review new users weekly
3. **Payment Review**: Verify failed payments
4. **Content Updates**: Add new books regularly
5. **Backup Schedule**: Automated daily backups

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + B` | Go to Books |
| `Ctrl + U` | Go to Users |
| `Ctrl + P` | Go to Payments |
| `Ctrl + R` | Refresh data |

## Troubleshooting

### Dashboard not loading

- Check admin authentication
- Verify API connectivity
- Clear browser cache

### Stats not updating

- Refresh page (F5)
- Check timezone settings
- Verify data exists for period
