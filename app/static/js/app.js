 
    function showAlert(message) {
      Swal.fire({
        toast: true, // Enables toast mode for smaller, top-positioned alerts
        position: 'top-end', // Positions the alert in the top-right corner
        icon: 'warning',
        title: message,
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true
      });
    }

   

      function extend_subscription(sub_id) {
        
        // show a loading screen
        Swal.fire({
          title: 'Processing...',
          text: 'Please wait while we process your request.',
          allowOutsideClick: false,
          didOpen: () => {
            Swal.showLoading();
          }
        });

        const duration_months = document.getElementById(`months${sub_id}`).value;
        if (!duration_months) {
          showAlert("Please select a duration.");
          return;
        }

        const initiateUrl = `/pay/extend/${sub_id}/${duration_months}`;

       
        window.location.href = initiateUrl;
      }

    
  

 

