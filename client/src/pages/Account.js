import React, { useState, useEffect } from "react";
import {
  getInstanceUrl,
  getLoggedInUser,
  createPaymentIntent,
  pauseStripePaymentSchedule,
  startStripePaymentSchedule,
  setSupabaseUserStatusToPaid,
} from "./../components/Api/Api";
import StripeWrapper from "./../components/StripeWrapper/StripeWrapper";
import {
  useStripe,
  useElements,
  PaymentElement,
} from "@stripe/react-stripe-js";
import {
  Box,
  Typography,
  Avatar,
  Link,
  CircularProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
} from "@mui/material";

/**
 * @typedef {import('types').User} User
 */

const CheckoutForm = ({ onSubscriptionComplete, userEmail }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [error, setError] = useState(null);
  const [processing, setProcessing] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!stripe || !elements) {
      return;
    }
    setProcessing(true);

    try {
      const { error: submitError } = await elements.submit();
      if (submitError) {
        setError(submitError.message);
        setProcessing(false);
        return;
      }

      const response = await startStripePaymentSchedule(userEmail);
      if (response.success) {
        const { clientSecret } = response.data[0];
        const result = await stripe.confirmPayment({
          elements,
          clientSecret,
          redirect: "if_required",
        });

        if (result.error) {
          setError(result.error.message);
        } else if (
          result.paymentIntent &&
          result.paymentIntent.status === "succeeded"
        ) {
          await onSubscriptionComplete();
          // Handle successful payment here without redirecting
          // For example, update UI, show a success message, etc.
          setSuccess(true);
        }
      } else {
        setError(response.message);
      }
    } catch (err) {
      setError("An unexpected error occurred.");
    }
    setProcessing(false);
  };

  return (
    <form onSubmit={handleSubmit}>
      <PaymentElement />
      {error && <Typography color="error">{error}</Typography>}
      <Button
        type="submit"
        disabled={!stripe || processing}
        variant="contained"
        color="primary"
        sx={{ mt: 2 }}
      >
        {processing ? <CircularProgress size={24} /> : "Subscribe"}
      </Button>
    </form>
  );
};

const Account = () => {
  const [clientSecret, setClientSecret] = useState(null);
  /** @type {[User, Function]} */
  const [user, setUser] = useState({
    id: 0,
    firstName: "",
    lastName: "",
    email: "",
    username: "",
    photoUrl: "",
  });
  const [userStatus, setUserStatus] = useState("not paid");
  const [instanceUrl, setInstanceUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openUpgradeDialog, setOpenUpgradeDialog] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [userResponse, instanceUrlResponse] = await Promise.all([
          getLoggedInUser(),
          getInstanceUrl(),
        ]);

        if (userResponse.success && instanceUrlResponse.success) {
          setUser(userResponse.data[0]);
          setInstanceUrl(instanceUrlResponse.data[0]);
          setUserStatus(userResponse.data[0].status);
        } else {
          setError("Failed to fetch user data or instance URL");
        }
      } catch (error) {
        setError("An error occurred while fetching data");
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };

    const fetchClientSecret = async () => {
      try {
        const response = await createPaymentIntent();
        if (response.success) {
          setClientSecret(response.data[0].clientSecret);
        } else {
          setError("Failed to create payment intent");
        }
      } catch (error) {
        setError("An error occurred while setting up payment");
        console.error("Error setting up payment:", error);
      }
    };

    fetchClientSecret();
    fetchData();
  }, []);

  /**
   * @returns {Promise<void>}
   */
  const handlePauseMembership = async () => {
    try {
      const response = await pauseStripePaymentSchedule(user.id, user.email);
      if (response.success) {
        setSnackbarOpen(true);
        setUserStatus("paused");
      } else {
        setError("Failed to pause membership");
      }
    } catch (error) {
      setError("An error occurred while pausing membership");
      console.error("Error pausing membership:", error);
    }
  };

  const handleUpgradeClick = () => {
    setOpenUpgradeDialog(true);
  };

  const handleCloseUpgradeDialog = () => {
    setOpenUpgradeDialog(false);
  };

  const handleSubscriptionComplete = () => {
    setSnackbarOpen(true);
    handleCloseUpgradeDialog();
    setSupabaseUserStatusToPaid(user.id);
  };

  if (loading) {
    return <CircularProgress />;
  }

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  return (
    <Box display="flex" flexDirection="column" alignItems="center">
      <Avatar
        src={user.photoUrl}
        alt={`${user.firstName} ${user.lastName}`}
        sx={{ width: 100, height: 100, marginBottom: 2 }}
      />
      <Typography variant="h4" gutterBottom>
        Account Information
      </Typography>
      <Typography variant="body1">
        Name:{" "}
        <Link
          href={`${instanceUrl}/${user.id}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          {user.firstName} {user.lastName}
        </Link>
      </Typography>
      <Typography variant="body1">Email: {user.email}</Typography>
      <Typography variant="body1">Username: {user.username}</Typography>

      {userStatus === "paid" ? (
        <Button
          variant="contained"
          color="info"
          onClick={handlePauseMembership}
          sx={{ marginTop: 2, backgroundColor: "grey.500", color: "white" }}
        >
          Pause Membership
        </Button>
      ) : (
        <Button
          variant="contained"
          color="primary"
          onClick={handleUpgradeClick}
          sx={{ marginTop: 2 }}
        >
          Upgrade to Paid
        </Button>
      )}

      <Dialog open={openUpgradeDialog} onClose={handleCloseUpgradeDialog}>
        <DialogTitle>Upgrade to Paid Plan</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Subscribe to our premium plan for $20/month
          </Typography>
          {clientSecret && user.email && (
            <StripeWrapper options={{ clientSecret }}>
              <CheckoutForm
                onSubscriptionComplete={handleSubscriptionComplete}
                userEmail={user.email}
              />
            </StripeWrapper>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseUpgradeDialog}>Cancel</Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        message="Successfully subscribed to premium plan!"
      />
    </Box>
  );
};

export default Account;
