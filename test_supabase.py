#!/usr/bin/env python3
"""
Supabase Database Test Script for Resume Modifier Extension
This script tests all major database operations and storage functionality.
"""

import os
import json
import tempfile
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SupabaseTestSuite:
    def __init__(self):
        """Initialize Supabase client with your credentials"""
        print("early")
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables")
        
        print("create client")
        print(self.supabase_url)
        print(self.supabase_key)
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        print("test user")
        self.test_user = None
        self.test_email = os.getenv('SUPABASE_EMAIL')
        self.test_password = os.getenv('SUPABASE_PASSWORD')
        print("HERE")
        
        print(f"🚀 Initializing tests with Supabase URL: {self.supabase_url}")
        print(f"📧 Test email: {self.test_email}")
        print("=" * 60)

    def test_1_connection(self):
        """Test basic connection to Supabase"""
        print("\n1️⃣ Testing database connection...")
        try:
            # Test by fetching resume templates
            response = self.supabase.table('resume_templates').select('*').execute()
            print(f"✅ Connection successful! Found {len(response.data)} resume templates")
            
            # Display templates
            for template in response.data:
                print(f"   - {template['name']}: {template['description']}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            return False

    def test_2_user_registration(self):
        """Test user registration"""
        print("\n2️⃣ Testing user registration...")
        try:
            # Register new user
            auth_response = self.supabase.auth.sign_up({
                "email": self.test_email,
                "password": self.test_password
            })
            
            if auth_response.user:
                self.test_user = auth_response.user
                print(f"✅ User registered successfully!")
                print(f"   User ID: {self.test_user.id}")
                print(f"   Email: {self.test_user.email}")

                # Create user profile
                try:
                    profile_data = {
                        "id": self.test_user.id,
                        "full_name": "Test User",
                    }

                    profile_response = self.supabase.table('user_profiles').insert(profile_data).execute()
                    print("✅ User profile created!")
                except Exception as profile_error:
                    # Check if profile already exists
                    existing_profile = self.supabase.table('user_profiles').select('*').eq('id', self.test_user.id).execute()
                    if existing_profile.data:
                        print("✅ User profile already exists (skipping creation)")
                    else:
                        print(f"⚠️  Could not create user profile: {str(profile_error)}")
                        print("   This may be due to RLS policies. Please check your Supabase policies.")

                return True
            else:
                print("❌ User registration failed: No user returned")
                return False
                
        except Exception as e:
            print(f"❌ User registration failed: {str(e)}")
            return False

    def test_3_user_login(self):
        """Test user login"""
        print("\n3️⃣ Testing user login...")
        try:
            # Sign in with the test user
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": self.test_email,
                "password": self.test_password
            })
            
            if auth_response.user:
                self.test_user = auth_response.user
                print("✅ User login successful!")
                print(f"   Access token: {auth_response.session.access_token[:20]}...")
                return True
            else:
                print("❌ User login failed")
                return False
                
        except Exception as e:
            print(f"❌ User login failed: {str(e)}")
            return False

    def test_4_user_preferences(self):
        """Test user preferences operations"""
        print("\n4️⃣ Testing user preferences...")
        try:
            if not self.test_user:
                print("❌ No authenticated user available")
                return False
            
            # Insert user preferences
            preferences_data = {
                "user_id": self.test_user.id,
                "default_template": "modern",
                "default_tone": "professional",
                "always_include_sections": ["education", "experience", "skills"],
                "color_scheme": "blue"
            }
            
            insert_response = self.supabase.table('user_preferences').insert(preferences_data).execute()
            print("✅ User preferences inserted!")
            
            # Fetch user preferences
            fetch_response = self.supabase.table('user_preferences').select('*').eq('user_id', self.test_user.id).execute()
            
            if fetch_response.data:
                prefs = fetch_response.data[0]
                print(f"✅ Preferences retrieved!")
                print(f"   Template: {prefs['default_template']}")
                print(f"   Tone: {prefs['default_tone']}")
                print(f"   Sections: {prefs['always_include_sections']}")
                
                # Update preferences
                update_data = {"color_scheme": "green"}
                update_response = self.supabase.table('user_preferences').update(update_data).eq('user_id', self.test_user.id).execute()
                print("✅ Preferences updated!")
                
                return True
            else:
                print("❌ Could not retrieve preferences")
                return False
                
        except Exception as e:
            print(f"❌ User preferences test failed: {str(e)}")
            return False

    def create_test_pdf(self):
        """Create a simple test PDF file"""
        try:
            # Create a simple PDF content (this is just text for testing)
            # In real implementation, you'd use a proper PDF library like reportlab
            pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test Resume PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
290
%%EOF"""
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(pdf_content)
                return temp_file.name
                
        except Exception as e:
            print(f"❌ Could not create test PDF: {str(e)}")
            return None

    def test_5_file_storage(self):
        """Test file storage operations"""
        print("\n5️⃣ Testing file storage...")
        try:
            if not self.test_user:
                print("❌ No authenticated user available")
                return False

            # Create test PDF
            test_pdf_path = self.create_test_pdf()
            if not test_pdf_path:
                return False

            # Upload to master-resumes bucket
            file_path = f"{self.test_user.id}/test-resume.pdf"

            with open(test_pdf_path, 'rb') as file:
                file_content = file.read()

                # Try to remove existing file first
                try:
                    self.supabase.storage.from_('master-resumes').remove([file_path])
                except:
                    pass  # File might not exist

                # Upload new file
                upload_response = self.supabase.storage.from_('master-resumes').upload(
                    file_path,
                    file_content,
                    file_options={"cache-control": "3600", "content-type": "application/pdf"}
                )

            print("✅ File uploaded to storage!")
            print(f"   File path: {file_path}")

            # List files in user's folder
            list_response = self.supabase.storage.from_('master-resumes').list(self.test_user.id)

            if list_response:
                print(f"✅ Files listed! Found {len(list_response)} files:")
                for file_info in list_response:
                    print(f"   - {file_info['name']} ({file_info['metadata']['size']} bytes)")

            # Download the file
            download_response = self.supabase.storage.from_('master-resumes').download(file_path)

            if download_response:
                print("✅ File downloaded successfully!")
                print(f"   Downloaded {len(download_response)} bytes")

            # Clean up
            os.unlink(test_pdf_path)

            return True

        except Exception as e:
            import traceback
            print(f"❌ File storage test failed: {str(e)}")
            print(f"   Traceback: {traceback.format_exc()}")
            return False

    def test_6_master_resume_database(self):
        """Test master resume database operations"""
        print("\n6️⃣ Testing master resume database operations...")
        try:
            if not self.test_user:
                print("❌ No authenticated user available")
                return False
            
            # Insert master resume record
            resume_data = {
                "user_id": self.test_user.id,
                "file_path": f"{self.test_user.id}/test-resume.pdf",
                "original_filename": "test-resume.pdf",
                "file_size": 1024,
                "structured_data": {
                    "personal_info": {
                        "name": "Test User",
                        "email": "test@example.com",
                        "phone": "+1234567890"
                    },
                    "experience": [
                        {
                            "title": "Software Developer",
                            "company": "Tech Corp",
                            "duration": "2020-2023",
                            "description": "Developed web applications"
                        }
                    ],
                    "skills": ["Python", "JavaScript", "React", "SQL"],
                    "education": [
                        {
                            "degree": "Computer Science",
                            "university": "Tech University",
                            "year": "2020"
                        }
                    ]
                }
            }
            
            insert_response = self.supabase.table('master_resumes').insert(resume_data).execute()
            print("✅ Master resume record inserted!")
            
            # Fetch master resume
            fetch_response = self.supabase.table('master_resumes').select('*').eq('user_id', self.test_user.id).execute()
            
            if fetch_response.data:
                resume = fetch_response.data[0]
                print("✅ Master resume retrieved!")
                print(f"   File: {resume['original_filename']}")
                print(f"   Skills: {resume['structured_data']['skills']}")
                print(f"   Experience: {len(resume['structured_data']['experience'])} entries")
                
                return True
            else:
                print("❌ Could not retrieve master resume")
                return False
                
        except Exception as e:
            print(f"❌ Master resume database test failed: {str(e)}")
            return False

    def test_7_generated_resume_tracking(self):
        """Test generated resume tracking"""
        print("\n7️⃣ Testing generated resume tracking...")
        try:
            if not self.test_user:
                print("❌ No authenticated user available")
                return False
            
            # Insert generated resume record
            generated_resume_data = {
                "user_id": self.test_user.id,
                "job_title": "Senior Python Developer",
                "company_name": "Google",
                "job_description": "We are looking for an experienced Python developer to join our team...",
                "job_url": "https://careers.google.com/jobs/python-dev",
                "file_path": f"{self.test_user.id}/google-python-dev.pdf",
                "modifications_made": {
                    "emphasized_skills": ["Python", "Machine Learning", "Cloud Computing"],
                    "reordered_sections": ["experience", "skills", "projects", "education"],
                    "added_keywords": ["scalable", "distributed systems", "API development"],
                    "template_used": "modern"
                },
                "template_used": "modern"
            }
            
            insert_response = self.supabase.table('generated_resumes').insert(generated_resume_data).execute()
            print("✅ Generated resume record inserted!")
            
            # Fetch generated resumes
            fetch_response = self.supabase.table('generated_resumes').select('*').eq('user_id', self.test_user.id).execute()
            
            if fetch_response.data:
                resume = fetch_response.data[0]
                print("✅ Generated resume retrieved!")
                print(f"   Job: {resume['job_title']} at {resume['company_name']}")
                print(f"   Emphasized skills: {resume['modifications_made']['emphasized_skills']}")
                
                # Update with feedback
                update_data = {
                    "feedback_rating": 5,
                    "got_interview": True
                }
                update_response = self.supabase.table('generated_resumes').update(update_data).eq('id', resume['id']).execute()
                print("✅ Resume feedback updated!")
                
                return True
            else:
                print("❌ Could not retrieve generated resume")
                return False
                
        except Exception as e:
            print(f"❌ Generated resume tracking test failed: {str(e)}")
            return False

    def test_8_job_applications_tracking(self):
        """Test job applications tracking"""
        print("\n8️⃣ Testing job applications tracking...")
        try:
            if not self.test_user:
                print("❌ No authenticated user available")
                return False
            
            # Get the generated resume ID for linking
            generated_resume_response = self.supabase.table('generated_resumes').select('id').eq('user_id', self.test_user.id).limit(1).execute()
            
            generated_resume_id = None
            if generated_resume_response.data:
                generated_resume_id = generated_resume_response.data[0]['id']
            
            # Insert job application record
            job_app_data = {
                "user_id": self.test_user.id,
                "generated_resume_id": generated_resume_id,
                "job_url": "https://careers.google.com/jobs/python-dev",
                "company_name": "Google",
                "job_title": "Senior Python Developer",
                "status": "applied",
                "keywords_matched": ["Python", "API", "Cloud", "Machine Learning"]
            }
            
            insert_response = self.supabase.table('job_applications').insert(job_app_data).execute()
            print("✅ Job application record inserted!")
            
            # Fetch job applications
            fetch_response = self.supabase.table('job_applications').select('*').eq('user_id', self.test_user.id).execute()
            
            if fetch_response.data:
                job_app = fetch_response.data[0]
                print("✅ Job application retrieved!")
                print(f"   Position: {job_app['job_title']} at {job_app['company_name']}")
                print(f"   Status: {job_app['status']}")
                print(f"   Keywords matched: {job_app['keywords_matched']}")
                
                return True
            else:
                print("❌ Could not retrieve job application")
                return False
                
        except Exception as e:
            print(f"❌ Job applications tracking test failed: {str(e)}")
            return False

    def test_9_analytics_queries(self):
        """Test analytics and reporting queries"""
        print("\n9️⃣ Testing analytics queries...")
        try:
            if not self.test_user:
                print("❌ No authenticated user available")
                return False
            
            # Get user's resume statistics
            generated_count_response = self.supabase.table('generated_resumes').select('id', count='exact').eq('user_id', self.test_user.id).execute()
            generated_count = generated_count_response.count
            
            applications_count_response = self.supabase.table('job_applications').select('id', count='exact').eq('user_id', self.test_user.id).execute()
            applications_count = applications_count_response.count
            
            # Get success rate
            interview_response = self.supabase.table('generated_resumes').select('got_interview').eq('user_id', self.test_user.id).execute()
            interviews = sum(1 for resume in interview_response.data if resume.get('got_interview'))
            
            print("✅ Analytics computed successfully!")
            print(f"   Generated resumes: {generated_count}")
            print(f"   Job applications: {applications_count}")
            print(f"   Interviews secured: {interviews}")
            if generated_count > 0:
                print(f"   Success rate: {(interviews/generated_count)*100:.1f}%")
            
            return True
            
        except Exception as e:
            print(f"❌ Analytics queries test failed: {str(e)}")
            return False

    def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        try:
            if not self.test_user:
                print("⚠️ No test user to clean up")
                return
            
            # Delete in reverse order due to foreign key constraints
            self.supabase.table('job_applications').delete().eq('user_id', self.test_user.id).execute()
            self.supabase.table('generated_resumes').delete().eq('user_id', self.test_user.id).execute()
            self.supabase.table('master_resumes').delete().eq('user_id', self.test_user.id).execute()
            self.supabase.table('user_preferences').delete().eq('user_id', self.test_user.id).execute()
            self.supabase.table('user_profiles').delete().eq('id', self.test_user.id).execute()
            
            # Delete files from storage
            try:
                self.supabase.storage.from_('master-resumes').remove([f"{self.test_user.id}/test-resume.pdf"])
            except:
                pass  # File might not exist
            
            print("✅ Test data cleaned up!")
            
        except Exception as e:
            print(f"⚠️ Cleanup warning: {str(e)}")

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🧪 SUPABASE DATABASE TEST SUITE")
        print("=" * 60)
        
        tests = [
            self.test_1_connection,
            self.test_2_user_registration,
            self.test_3_user_login,
            self.test_4_user_preferences,
            self.test_5_file_storage,
            self.test_6_master_resume_database,
            self.test_7_generated_resume_tracking,
            self.test_8_job_applications_tracking,
            self.test_9_analytics_queries
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
                failed += 1
        
        # Cleanup
        self.cleanup()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Your Supabase setup is working perfectly!")
        else:
            print(f"\n⚠️ {failed} tests failed. Please check the error messages above.")
        
        return failed == 0


def main():
    """Main function to run the test suite"""
    print("Setting up test environment...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("\n❌ .env file not found!")
        print("Please create a .env file with:")
        print("SUPABASE_URL=your_supabase_url")
        print("SUPABASE_ANON_KEY=your_anon_key")
        return
    
    try:
        print("test suite")
        test_suite = SupabaseTestSuite()
        test_suite.run_all_tests()
    except Exception as e:
        print(f"❌ Failed to initialize test suite: {str(e)}")
        print("\nPlease check your environment variables and Supabase setup.")


if __name__ == "__main__":
    main()