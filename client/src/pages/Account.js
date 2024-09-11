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
  Paper,
  Divider,
} from "@mui/material";

/**
 * @typedef {import('types').User} User
 */

/**
 * @param {object} props
 * @param {() => void} props.onSubscriptionComplete
 * @param {string} props.userEmail
 */
const CheckoutForm = ({ onSubscriptionComplete, userEmail }) => {
  const stripe = useStripe();
  const elements = useElements();

  /**
   * @type {[string | undefined, React.Dispatch<React.SetStateAction<string | undefined>>]}
   */
  const [error, setError] = useState(/** @type {string | undefined} */(undefined));
  const [processing, setProcessing] = useState(false);

  /**
   * @param {React.FormEvent<HTMLFormElement>} event
   */
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
          // TODO: is await needed in here?
          await onSubscriptionComplete();
          // Handle successful payment here without redirecting
          // For example, update UI, show a success message, etc.

          // commented temporary
          // setSuccess(true);
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

/**
 * @param {object} props
 * @param {string} props.subtitle
 * @param {string} props.title
 * @param {string} props.description
 * @param {string} [props.buttonText = ""]
 * @param {(event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => void} props.onButtonClick
 */
const SubscriptionAlertCard = ({ subtitle, title, description, buttonText = "", onButtonClick }) => {
  return (
    <Box sx={{ marginTop: "24px", width: "100%", display: "flex", justifyContent: "center" }}>
      <Paper
        elevation={3}
        sx={{
          width: "852px",
          borderRadius: "50px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          padding: "34px 67px 47px",
          boxShadow: "2px 13px 20.5px 1px #0000001A"
        }}
      >
        <Typography
          variant="body1"
          sx={{
            marginBottom: "14px",
            lineHeight: "1",
            letterSpacing: "4.76px",
            fontWeight: "500",
            textAlign: "center",
            color: "#1E242F"
          }}
        >{subtitle}</Typography>
        <Typography
          variant="h1"
          sx={{
            color: "#1E242F",
            marginBottom: "28px",
            letterSpacing: "-1.62px",
            textAlign: "center"
          }}
        >{title}</Typography>
        <Typography variant="body2"
          sx={{
            marginBottom: "40px",
            textAlign: "center",
            color: "#4C4C4C"
          }}
        >
          {description}
        </Typography>

        <Button
          onClick={onButtonClick}
          sx={{
            background: "linear-gradient(168deg, #FF7D2F 24.98%, #491EFF 97.93%)",
            height: "57px",
            width: "388px",
            borderRadius: "40px",
            color: "white",
            fontSize: "32px",
            letterSpacing: "-0.96px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            textTransform: "none"
          }}
        >
          {buttonText}
        </Button>
      </Paper>
    </Box>
  )
}

const Account = () => {
  const [clientSecret, setClientSecret] = useState(null);

  /**
   * @type {[User, React.Dispatch<React.SetStateAction<User>>]}
   */
  const [user, setUser] = useState({
    id: "0",
    firstName: "Peter",
    lastName: "User",
    email: "datalover@gmail.com",
    username: "testuser123",
    photoUrl: "",
    status: "not paid"
  });
  const [userStatus, setUserStatus] = useState("not paid");
  const [instanceUrl, setInstanceUrl] = useState("");
  const [loading, setLoading] = useState(true);

  /**
   * @type {[string | null, React.Dispatch<React.SetStateAction<string | null>>]}
   */
  const [error, setError] = useState(/** @type{string | null} */(null));
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
    <Box display="flex" flexDirection="column">
      <Box sx={{ display: "flex", flexDirection: "row", alignItems: "center", justifyContent: "start", padding: "34px 44px" }}>
        <Box sx={{ display: "flex", flexDirection: "row", gap: "20px", alignItems: "center", justifyContent: "start", }}>
          <Avatar
            src={user.photoUrl}
            alt={`${user.firstName} ${user.lastName}`}
            sx={{ width: 80, height: 80, marginBottom: 2 }}
          />
          <Typography variant="h4" gutterBottom sx={{ fontSize: "24px", fontWeight: "400", lineHeight: "1.48", letterSpacing: "-0.72px" }}>
            Account Information
          </Typography>
        </Box>

        <Divider
          sx={{
            marginLeft: "34px",
            marginRight: "54px",
            height: "68px",
            width: "1px",
            border: "none",
            backgroundColor: "#DDDDDD"
          }}
        />

        <Box sx={{ display: "flex", flexDirection: "row", gap: "68px", alignItems: "center", justifyContent: "start", }}>
          <Box sx={{ display: "flex", flexDirection: "column", gap: "0px" }}>
            <Typography variant="body1" sx={{ fontWeight: "500", fontSize: "12px", lineHeight: "1.78", color: "#4C4C4C" }}>
              NAME:{" "}
            </Typography>
            <Link
              href={`${instanceUrl}/${user.id}`}
              target="_blank"
              rel="noopener noreferrer"
              sx={{ fontSize: "18px", lineHeight: "1.78", color: "#533AF3" }}
            >
              {user.firstName} {user.lastName}
            </Link>
          </Box>

          <Box sx={{ display: "flex", flexDirection: "column", }}>
            <Typography variant="body1" sx={{ fontWeight: "500", fontSize: "12px", lineHeight: "1.78", color: "#4C4C4C" }}>
              EMAIL:
            </Typography>
            <Typography sx={{ fontSize: "18px", lineHeight: "1.78", color: "#533AF3" }}>{user.email}</Typography>
          </Box>

          <Box sx={{ display: "flex", flexDirection: "column", }}>
            <Typography variant="body1" sx={{ fontWeight: "500", fontSize: "12px", lineHeight: "1.78", color: "#4C4C4C" }}>USERNAME:</Typography>
            <Typography sx={{ fontSize: "18px", lineHeight: "1.78", color: "#533AF3" }}>{user.username}</Typography>
          </Box>
        </Box>
      </Box>



      {userStatus === "paid" && (
        <SubscriptionAlertCard
          title="You are upgraded!"
          subtitle="Awesome"
          description="Your membership has been upgraded! Enjoy unlimited access to all premium features and exclusive benefits. Dive in and make the most of your enhanced experience."
          buttonText="Pause Membership"
          onButtonClick={handlePauseMembership}
        />
      )}

      {userStatus === "paused" && (
        <SubscriptionAlertCard
          title="Don't Miss Out!"
          subtitle="Membership on Paused!"
          description="Your membership is on hold, but don't worry — you can resume anytime to unlock all the perks again. We're here when you're ready!"
          buttonText="Resume Membership"
          onButtonClick={handleUpgradeClick}
        />
      )}

      {
        (userStatus === "not paid" || !userStatus) && (
          <SubscriptionAlertCard
            title="HEADS UP!"
            subtitle="Your free trial is over"
            description="Your free trial has ended, but the perks don't have to stop! Upgrade now to keep enjoying all the premium features and exclusive benefits."
            buttonText="Upgrade to Paid"
            onButtonClick={handleUpgradeClick}
          />

        )
      }

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
    </Box >
  );
};

export default Account;
