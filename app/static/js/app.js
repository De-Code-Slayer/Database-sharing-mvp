 
    function showAlert(message) {
      Swal.fire({
        toast: true, // Enables toast mode for smaller, top-positioned alerts
        position: 'top-end', // Positions the alert in the top-right corner
        icon: 'success',
        title: message,
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true
      });
    }
  