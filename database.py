import motor.motor_asyncio
import datetime
import os

class Database:
    def __init__(self, uri, database_name): # Corrected: Changed init back to __init__
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.user
        self.premium = self.db.premium

    async def get_user_language(self, user_id):  # Corrected: Indented inside class
        """
        Retrieves the language code for a user from the database.
        Returns the language code (e.g., 'en', 'ar') or None if not set.
        """
        user_data = await self.get_user_data(user_id)
        if user_data and 'language_code' in user_data:
            return user_data['language_code']
        return None

    async def set_user_language(self, user_id, language_code): # Corrected: Indented inside class
        """
        Sets the language code for a user in the database.
        """
        await self.update_user_data(user_id, {'language_code': language_code})

    def new_user(self, id):
        """Creates a new user document."""
        return dict(
            _id=int(id),
            join_date=datetime.date.today().isoformat(),
            file_id=None,
            caption=None,
            prefix=None,
            suffix=None,
            used_limit=0,
            usertype="Free",
            uploadlimit=1073741824,
            daily=0,
            metadata_mode=False,
            metadata_code="--change-title @X_XF8\n--change-video-title @X_XF8\n--change-audio-title @X_XF8\n--change-subtitle-title @X_XF8\n--change-author @X_XF8",
            expiry_time=None,
            has_free_trial=False,
            ban_status=dict(
                is_banned=False,
                ban_duration=0,
                banned_on=datetime.date.max.isoformat(),
                ban_reason=''
            ),
            language_code=None # ADDED: Initialize language_code in new_user
        )

    async def add_user(self, b, u):
        """Adds a new user to the database if they don't exist."""
        if not await self.is_user_exist(u.id):
            user = self.new_user(u.id)
            await self.col.insert_one(user)
            # await send_log(b, u)  # You had a send_log function, replace if needed

    async def is_user_exist(self, id):
        """Checks if a user exists in the database."""
        user = await self.col.find_one({'_id': int(id)})
        return bool(user)

    async def total_users_count(self):
        """Returns the total number of users."""
        count = await self.col.count_documents({})
        return count

    async def total_premium_users_count(self):
        """Returns the total number of premium users."""
        count = await self.premium.count_documents({})
        return count

    async def get_all_users(self):
        """Returns all users in the database."""
        all_users = self.col.find({})
        return all_users

    async def delete_user(self, user_id):
        """Deletes a user from the database."""
        await self.col.delete_many({'_id': int(user_id)})

    async def set_thumbnail(self, id, file_id):
        """Sets the thumbnail file ID for a user."""
        await self.col.update_one({'_id': int(id)}, {'$set': {'file_id': file_id}})

    async def get_thumbnail(self, id):
        """Retrieves the thumbnail file ID for a user."""
        user = await self.col.find_one({'_id': int(id)})
        return user.get('file_id', None)

    async def get_user(self, user_id):
        """Retrieves premium user data."""
        user_data = await self.premium.find_one({"id": user_id})
        return user_data

    async def addpremium(self, user_id, expiry_time):
        """Adds or updates premium status for a user."""
        user_data = {"id": user_id, "expiry_time": expiry_time}
        await self.premium.update_one({"id": user_id}, {"$set": user_data}, upsert=True)
        await self.col.update_one({'_id': user_id}, {'$set': {'usertype': "Pro",'uploadlimit': float('inf')}})

    async def remove_premium(self, user_id):
        """Removes premium status from a user."""
        await self.premium.update_one({"id": user_id}, {"$set": {"expiry_time": None}})
        await self.col.update_one({'_id': user_id}, {'$set': {'usertype': "Free", 'uploadlimit': 1073741824}})

    async def has_premium_access(self, user_id): # Renamed to is_premium_user
        """Checks if a user has active premium access."""
        user_data = await self.get_user(user_id)
        if user_data:
            expiry_time = user_data.get("expiry_time")
            if expiry_time is not None and isinstance(expiry_time, datetime.datetime) and datetime.datetime.now() <= expiry_time:
                return True
            else:
                await self.remove_premium(user_id)
                return False
        return False

    async def is_premium_user(self, user_id): # Added is_premium_user alias for has_premium_access for backward compatibility or different naming preference in main.py
        """Alias for has_premium_access. Checks if a user has active premium access."""
        return await self.has_premium_access(user_id)


    async def get_user_data(self, user_id):
        """Retrieves complete user data from the user collection."""
        user_data = await self.col.find_one({'_id': int(user_id)})
        return user_data

    async def update_user_data(self, user_id, data): # Added this method - important for set_user_language
        """Updates user data in the database."""
        await self.col.update_one({'_id': int(user_id)}, {'$set': data}, upsert=True)


# --- Initialize Database Instance ---

DB_URL = os.environ.get("MONGODB_URI", "mongodb+srv://mrhex86:mrhex86@cluster0.8pxiirj.mongodb.net/?retryWrites=true&w=majority")
DB_NAME = os.environ.get("MONGODB_DATABASE_NAME") or "telegram_bot_db"
digital_botz = Database(DB_URL, DB_NAME)
