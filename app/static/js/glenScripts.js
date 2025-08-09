document.addEventListener('DOMContentLoaded', function () {
            const calendarEl = document.getElementById('calendar');
            const medicationModal = new bootstrap.Modal(document.getElementById('medicationModal'));
            const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
            const errorAlert = document.getElementById('errorAlert');
            const form = document.getElementById('medicationForm');
            
            let currentEditingId = null;
            let isMobile = window.innerWidth <= 768;

            // Handle window resize
            window.addEventListener('resize', function() {
                isMobile = window.innerWidth <= 768;
                calendar.render();
            });

            // Initialize calendar with responsive settings
            window.calendar = new FullCalendar.Calendar(calendarEl, {
                customButtons: {
                    addMedication: {
                        text: isMobile ? '💊' : '💊 Add Medication',
                        click: function() {
                            window.location.href = '/add_medication';
                        }
                    },
                    addSeizure: {
                        text: isMobile ? '⚡' : '⚡ Track Seizure',
                        click: function() {
                            window.location.href = '/add_seizure';
                        }
                    }
                },
                header: false,
                plugins: ['dayGrid', 'interaction'],
                editable: false,
                selectable: !isMobile, // Disable selection on mobile to prevent conflicts
                displayEventTime: true,
                events: '/api/events',
                height: isMobile ? 'auto' : 600,
                contentHeight: isMobile ? 'auto' : 550,
                aspectRatio: isMobile ? 1.0 : 1.35,
                
                datesSet: function(info) {
                    document.getElementById('calendarTitle').textContent = info.view.title;
                },

                eventRender: function(info) {
                    // Add context menu to events and styling based on type
                    if (isMobile) {
                        // On mobile, use tap and hold for context menu
                        let touchTimer;
                        info.el.addEventListener('touchstart', function(e) {
                            touchTimer = setTimeout(function() {
                                e.preventDefault();
                                showContextMenu(e.touches[0], info.event);
                            }, 500); // 500ms hold
                        });
                        
                        info.el.addEventListener('touchend', function() {
                            clearTimeout(touchTimer);
                        });
                        
                        info.el.addEventListener('touchmove', function() {
                            clearTimeout(touchTimer);
                        });
                    } else {
                        info.el.addEventListener('contextmenu', function(e) {
                            e.preventDefault();
                            showContextMenu(e, info.event);
                        });
                    }

                    // Add different styling for different event types
                    if (info.event.extendedProps.type === 'seizure') {
                        info.el.style.fontWeight = 'bold';
                        info.el.style.border = '2px solid #dc3545';
                    } else if (info.event.extendedProps.type === 'medication') {
                        info.el.style.border = '2px solid #28a745';
                    }
                },
                
                select: function(info) {
                    if (!isMobile) {
                        showSelectionMenu(info);
                    }
                },

                eventClick: function(info) {
                    if (isMobile) {
                        // On mobile, single tap shows context menu
                        showContextMenu(info.jsEvent, info.event);
                    }
                }
            });

            function showSelectionMenu(info) {
                const startDate = moment(info.start).format('YYYY-MM-DD');
                let endDate = moment(info.end).subtract(1, 'day').format('YYYY-MM-DD');
                
                if (startDate === endDate) {
                    endDate = '';
                }

                // Create a simple selection modal
                const selectionModal = document.createElement('div');
                selectionModal.className = 'modal fade';
                selectionModal.id = 'selectionModal';
                selectionModal.innerHTML = `
                    <div class="modal-dialog modal-sm">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Add Entry for ${startDate}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body selection-modal-body text-center">
                                <a href="/add_medication?date=${startDate}" class="btn btn-success selection-btn w-100">
                                    💊 Add Medication
                                </a>
                                <a href="/add_seizure?date=${startDate}" class="btn btn-danger selection-btn w-100">
                                    ⚡ Track Seizure
                                </a>
                            </div>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(selectionModal);
                const modal = new bootstrap.Modal(selectionModal);
                modal.show();
                
                // Clean up after modal is hidden
                selectionModal.addEventListener('hidden.bs.modal', function() {
                    selectionModal.remove();
                });
            }

            calendar.render();
            document.getElementById('calendarTitle').textContent = calendar.view.title;

            // Show flash messages if any
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('success')) {
                showSuccess(decodeURIComponent(urlParams.get('success')));
            }
            if (urlParams.get('error')) {
                showError(decodeURIComponent(urlParams.get('error')));
            }

            function showSuccess(message) {
                // Create a temporary success alert
                const successAlert = document.createElement('div');
                successAlert.className = 'alert alert-success alert-dismissible fade show position-fixed';
                successAlert.style.top = '20px';
                successAlert.style.right = '20px';
                successAlert.style.zIndex = '9999';
                successAlert.style.maxWidth = isMobile ? 'calc(100% - 40px)' : '400px';
                successAlert.innerHTML = `
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                document.body.appendChild(successAlert);

                // Auto-remove after 4 seconds
                setTimeout(() => {
                    if (successAlert.parentNode) {
                        successAlert.remove();
                    }
                }, 4000);
            }

            function showError(message) {
                // Create a temporary error alert
                const errorAlert = document.createElement('div');
                errorAlert.className = 'alert alert-danger alert-dismissible fade show position-fixed';
                errorAlert.style.top = '20px';
                errorAlert.style.right = '20px';
                errorAlert.style.zIndex = '9999';
                errorAlert.style.maxWidth = isMobile ? 'calc(100% - 40px)' : '400px';
                errorAlert.innerHTML = `
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                document.body.appendChild(errorAlert);

                // Auto-remove after 4 seconds
                setTimeout(() => {
                    if (errorAlert.parentNode) {
                        errorAlert.remove();
                    }
                }, 4000);
            }

            function showContextMenu(e, event) {
                // Remove existing context menu
                document.querySelectorAll('.context-menu').forEach(menu => menu.remove());
                
                const menu = document.createElement('div');
                menu.className = 'context-menu';
                
                const eventType = event.extendedProps.type;
                const eventId = event.id.replace(/^(med_|seizure_)/, ''); // Remove prefix
                
                if (eventType === 'medication') {
                    menu.innerHTML = `
                        <ul>
                            <li data-action="edit" data-id="${eventId}" data-type="medication">
                                <i class="fas fa-edit"></i>Edit Medication
                            </li>
                            <li data-action="delete" data-id="${eventId}" data-type="medication">
                                <i class="fas fa-trash-alt"></i>Delete Medication
                            </li>
                        </ul>
                    `;
                } else if (eventType === 'seizure') {
                    menu.innerHTML = `
                        <ul>
                            <li data-action="edit" data-id="${eventId}" data-type="seizure">
                                <i class="fas fa-edit"></i>Edit Seizure
                            </li>
                            <li data-action="delete" data-id="${eventId}" data-type="seizure">
                                <i class="fas fa-trash-alt"></i>Delete Seizure
                            </li>
                        </ul>
                    `;
                }
                
                document.body.appendChild(menu);
                
                // Position menu responsively
                let x = e.pageX || e.clientX;
                let y = e.pageY || e.clientY;
                
                // Adjust for mobile screens
                if (isMobile) {
                    x = Math.min(x, window.innerWidth - 200);
                    y = Math.min(y, window.innerHeight - 120);
                }
                
                menu.style.top = y + 'px';
                menu.style.left = x + 'px';
                
                // Handle menu clicks
                menu.addEventListener('click', function(e) {
                    const li = e.target.closest('li');
                    const action = li.dataset.action;
                    const id = li.dataset.id;
                    const type = li.dataset.type;
                    menu.remove();
                    
                    if (action === 'edit') {
                        if (type === 'medication') {
                            window.location.href = `/edit_medication/${id}`;
                        } else if (type === 'seizure') {
                            window.location.href = `/edit_seizure/${id}`;
                        }
                    } else if (action === 'delete') {
                        showDeleteConfirmation(id, type, event.title);
                    }
                });
                
                // Remove menu when clicking elsewhere
                const closeMenu = function(e) {
                    if (!menu.contains(e.target)) {
                        menu.remove();
                        document.removeEventListener('click', closeMenu);
                        document.removeEventListener('touchstart', closeMenu);
                    }
                };
                
                setTimeout(() => {
                    document.addEventListener('click', closeMenu);
                    document.addEventListener('touchstart', closeMenu);
                }, 100);
            }

            function showDeleteConfirmation(id, type, title) {
                const confirmed = confirm(`Are you sure you want to delete "${title}"?`);
                if (confirmed) {
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.action = type === 'medication' ? `/delete_medication/${id}` : `/delete_seizure/${id}`;
                    document.body.appendChild(form);
                    form.submit();
                }
            }

            // Set default time to 9:00 AM
            document.getElementById('time_to_take').value = '09:00';

            // Handle form submission with loading state
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                const submitBtn = document.getElementById('submitBtn');
                const originalText = submitBtn.innerHTML;
                
                // Show loading state
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Saving...';
                submitBtn.disabled = true;
                
                // Simulate form submission (replace with actual logic)
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 1000);
            });

            // Clear errors when modal is hidden
            document.getElementById('medicationModal').addEventListener('hide.bs.modal', function() {
                hideErrors();
                form.reset();
                document.getElementById('time_to_take').value = '09:00';
            });

            function hideErrors() {
                errorAlert.style.display = 'none';
            }

            // Prevent zoom on iOS when focusing inputs
            if (isMobile && /iPad|iPhone|iPod/.test(navigator.userAgent)) {
                const inputs = document.querySelectorAll('input, select, textarea');
                inputs.forEach(input => {
                    input.addEventListener('focus', function() {
                        this.style.fontSize = '16px';
                    });
                });
            }

            // Handle orientation change
            window.addEventListener('orientationchange', function() {
                setTimeout(() => {
                    calendar.render();
                }, 500);
            });

            // Improve touch scrolling on mobile
            if (isMobile) {
                document.body.style.webkitOverflowScrolling = 'touch';
                
                // Add pull-to-refresh functionality
                let startY = 0;
                let isRefreshing = false;
                
                document.addEventListener('touchstart', function(e) {
                    startY = e.touches[0].pageY;
                }, { passive: true });
                
                document.addEventListener('touchmove', function(e) {
                    const y = e.touches[0].pageY;
                    if (y > startY + 100 && window.pageYOffset === 0 && !isRefreshing) {
                        isRefreshing = true;
                        // Simple refresh indicator
                        const refreshIndicator = document.createElement('div');
                        refreshIndicator.className = 'alert alert-info position-fixed w-100';
                        refreshIndicator.style.top = '0';
                        refreshIndicator.style.zIndex = '10000';
                        refreshIndicator.innerHTML = '↻ Refreshing calendar...';
                        document.body.appendChild(refreshIndicator);
                        
                        // Refresh calendar events
                        calendar.refetchEvents();
                        
                        setTimeout(() => {
                            refreshIndicator.remove();
                            isRefreshing = false;
                        }, 1000);
                    }
                }, { passive: true });
            }
            

        });