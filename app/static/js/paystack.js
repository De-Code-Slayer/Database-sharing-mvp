

document.addEventListener('DOMContentLoaded', function () {
    
    const paystackButton = document.getElementById('paystack-button');
    const email = paystackButton.dataset.email;
    const amount = paystackButton.dataset.amount;
    const paystackKey = paystackButton.dataset.paystackKey;
    const initiateUrl = paystackButton.dataset.initiateUrl;

    paystackButton.addEventListener('click', async function () {
        // gtag('event', 'paystack_click', {
        //     'event_category': 'payment',
        //     'event_label': 'Paystack Button Clicked'
        // });

        
        if (amount === null) return; 
        
        if (!amount || isNaN(amount)) {
            gtag('event', 'paystack_invalid_amount', {
                'event_category': 'payment_error',
                'event_label': 'Invalid amount entered'
            });
            Swal.fire("Error", "Please enter a valid amount.", "error");
            return;
        }
        

        // gtag('event', 'paystack_amount_entered', {
        //     'event_category': 'payment',
        //     'event_label': 'Amount specified',
        //     'value': parseFloat(amount)
        // });
        
        // Show a loading alert while processing the payment initiation
                Swal.fire({
                    title: 'Processing...',
                    allowOutsideClick: false,
                    background: '#ffffffff',   // modal background
                    didOpen: () => Swal.showLoading()
                });

        fetch(initiateUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: amount * 100, email: email })
        })
        .then(
            response => response.json())
        .then(data => {
            gtag('event', 'paystack_initiated', {
                'event_category': 'payment',
                'event_label': 'Payment initiated',
                'value': parseFloat(amount),
                'currency': 'NGN'
            });

            Swal.close(); // Close the loading alert
            const handler = PaystackPop.setup({
                key: paystackKey,
                email: data.email,
                amount: data.amount,
                ref: data.reference,
                onClose: function () {
                    gtag('event', 'paystack_abandoned', {
                        'event_category': 'payment',
                        'event_label': 'Popup closed without payment',
                        'value': parseFloat(amount),
                        'currency': 'NGN'
                    });
                    Swal.fire("Interrupted", "Payment process was interrupted.", "info");
                },
                callback: function (response) {
                    gtag('event', 'paystack_success', {
                        'event_category': 'payment',
                        'event_label': 'Payment completed',
                        'value': parseFloat(amount),
                        'currency': 'NGN',
                        'transaction_id': response.reference
                    });

                    Swal.fire("Success!", `Payment was successful. Reference: ${response.reference}`, "success");
                    window.location.reload();
                }
            });
            handler.openIframe();
        })
        .catch(error => {
            gtag('event', 'paystack_api_error', {
                'event_category': 'payment_error',
                'event_label': 'Initiation API failed',
                'value': parseFloat(amount)
            });
            console.error('Error:', error);
            alert('There was an issue with initiating the payment.');
        });
    });

});