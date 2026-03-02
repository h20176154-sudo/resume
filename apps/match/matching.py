import re
from collections import defaultdict
from typing import Dict, List, Tuple, Set

# Skill category mapping for better semantic understanding
SKILL_CATEGORIES = {
    "programming_languages": [
        "python", "java", "javascript", "typescript", "c++", "csharp", "c#",
        "php", "ruby", "swift", "kotlin", "go", "golang", "rust", "scala", "r"
    ],
    "frontend": [
        "react", "vue", "angular", "svelte", "nextjs", "gatsby", "html", "css",
        "flutter", "react native", "user interface", "user experience"
    ],
    "backend": [
        "django", "nodejs", "express", "fastapi", "flask", "spring", "laravel",
        "symfony", "hibernate", "rest", "api", "graphql"
    ],
    "databases": [
        "sql", "mongodb", "postgresql", "mysql", "oracle", "cassandra", "redis",
        "elasticsearch", "nosql", "snowflake", "bigquery"
    ],
    "devops_cloud": [
        "docker", "kubernetes", "aws", "azure", "gcp", "devops", "ci/cd",
        "jenkins", "circleci", "github", "gitlab", "terraform", "ansible"
    ],
    "data_science": [
        "machine learning", "data science", "data analysis", "tensorflow",
        "pytorch", "pandas", "numpy", "scikit", "big data", "spark", "hadoop",
        "natural language processing", "computer vision"
    ],
    "data_engineering": [
        "etl", "dbt", "airflow", "flink", "kafka", "fivetran", "confluent"
    ],
    "analytics_bi": [
        "tableau", "powerbi", "lookerstudio", "metabase", "data visualization",
        "business intelligence"
    ],
    "soft_skills": [
        "leadership", "communication", "project management", "product management",
        "agile", "scrum", "kanban", "problem solving", "team collaboration"
    ]
}

# Flatten category skills for quick lookup
CATEGORY_LOOKUP = {}
for category, skills in SKILL_CATEGORIES.items():
    for skill in skills:
        CATEGORY_LOOKUP[skill] = category

# Core vs. secondary skill importance weights
SKILL_IMPORTANCE = {
    "programming_languages": 1.0,
    "backend": 0.95,
    "frontend": 0.85,
    "databases": 0.9,
    "devops_cloud": 0.85,
    "data_science": 0.9,
    "data_engineering": 0.9,
    "analytics_bi": 0.75,
    "soft_skills": 0.6
}

# Experience level keywords
EXPERIENCE_LEVELS = {
    "senior": ["senior", "lead", "principal", "staff", "architect"],
    "mid": ["mid", "intermediate", "experienced"],
    "junior": ["junior", "entry", "recent", "graduate"]
}

# Education level keywords
EDUCATION_KEYWORDS = {
    "phd": ["phd", "doctorate", "doctoral degree"],
    "masters": ["master's", "masters", "mba", "ms"],
    "bachelors": ["bachelor", "b.s.", "b.a.", "bs", "ba"],
    "diploma": ["diploma", "certificate", "bootcamp"]
}

def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract skills from text with improved accuracy and categorization.
    Uses multi-word skill patterns and normalized matching.
    """
    text_lower = text.lower()
    found_skills = []
    
    # Extract multi-word skills first to prevent word boundary issues
    multi_word_skills = [
        "machine learning", "data analysis", "data science", "data engineering",
        "project management", "product management", "devops engineer",
        "cloud architecture", "systems design", "database administration",
        "front end", "back end", "full stack", "user experience", "user interface",
        "ci/cd", "test driven", "agile methodology", "scrum master",
        "business intelligence", "data visualization", "big data",
        "natural language processing", "computer vision", "react native",
        "kafka streams", "rest api", "api integration"
    ]
    
    for skill in multi_word_skills:
        if skill in text_lower:
            found_skills.append(skill)
    
    # Extract single-word skills
    word_skills = re.findall(r'\b[a-zA-Z][a-zA-Z0-9+\-#]*\b', text_lower)
    
    common_skills = [
        "python", "java", "javascript", "react", "nodejs", "django", "rest", "api",
        "sql", "mongodb", "html", "css", "aws", "docker", "git", "linux", "typescript",
        "excel", "bigquery", "spark", "flink", "kafka", "redis", "azure", "gcp",
        "snowflake", "postgresql", "mysql", "oracle", "nosql", "tableau", "tensorflow",
        "pytorch", "etl", "dbt", "airflow", "fivetran", "powerbi", "quicksight",
        "lookerstudio", "metabase", "cloud", "kubernetes", "terraform", "ansible",
        "jenkins", "github", "gitlab", "bitbucket", "jira", "confluence", "slack",
        "teamcity", "circleci", "travis", "prometheus", "grafana", "datadog", "splunk",
        "elasticsearch", "cassandra", "hadoop", "scala", "rust", "go", "golang", "c++",
        "csharp", "c#", "php", "ruby", "swift", "kotlin", "flutter", "vue",
        "angular", "svelte", "nextjs", "gatsby", "laravel", "symfony", "flask", "fastapi",
        "spring", "hibernate", "express", "graphql", "pandas", "numpy",
        "matplotlib", "scikit", "pytest", "jest", "mocha", "cypress", "selenium", "playwright",
        "bootstrap", "material", "tailwind"
    ]
    
    single_word_skills = []
    for word in word_skills:
        # Direct match
        if word in common_skills:
            single_word_skills.append(word)
        # Try removing numbers from the end (e.g., html5 -> html, css3 -> css)
        else:
            word_without_numbers = re.sub(r'\d+$', '', word)
            if word_without_numbers and word_without_numbers in common_skills:
                single_word_skills.append(word_without_numbers)
    
    found_skills.extend(single_word_skills)
    
    # Special handling: if "rest api" was found, ensure "api" is also included
    # since REST API typically includes working with APIs
    if "rest api" in found_skills and "api" not in found_skills:
        found_skills.append("api")
    if "api integration" in found_skills and "api" not in found_skills:
        found_skills.append("api")
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(found_skills))


def extract_experience_years(text: str) -> int:
    """Extract years of experience from text."""
    matches = re.findall(r'(\d+)\+?\s*(?:years?|yrs?|year|yr)', text.lower())
    if matches:
        return max(int(m) for m in matches)
    return 0


def extract_education_level(text: str) -> str:
    """Extract education level from text."""
    text_lower = text.lower()
    for level, keywords in EDUCATION_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            return level
    return "unknown"


def categorize_skills(skills: List[str]) -> Dict[str, List[str]]:
    """Categorize skills by type."""
    categorized = defaultdict(list)
    for skill in skills:
        category = CATEGORY_LOOKUP.get(skill, "other")
        categorized[category].append(skill)
    return dict(categorized)


def calculate_skill_match_score(profile_skills: List[str], job_skills: List[str], 
                                 profile_proficiency: Dict[str, int]) -> Tuple[float, List[str], List[str]]:
    """
    Calculate skill match score with weighted importance based on skill categories.
    Returns (score, matched_skills, unmatched_skills)
    """
    if not job_skills:
        return 100.0, profile_skills, []
    
    matched_skills = []
    unmatched_skills = []
    weighted_match = 0.0
    weighted_total = 0.0
    
    for job_skill in job_skills:
        skill_category = CATEGORY_LOOKUP.get(job_skill, "other")
        weight = SKILL_IMPORTANCE.get(skill_category, 0.5)
        weighted_total += weight
        
        if job_skill in profile_skills:
            matched_skills.append(job_skill)
            # Boost score if candidate has advanced proficiency
            proficiency_multiplier = 1.0
            if profile_proficiency.get("advanced", 0) > 0:
                proficiency_multiplier = 1.15
            weighted_match += weight * proficiency_multiplier
        else:
            unmatched_skills.append(job_skill)
    
    skill_match_percentage = (weighted_match / weighted_total * 100) if weighted_total > 0 else 0
    return skill_match_percentage, matched_skills, unmatched_skills


def calculate_experience_match(profile_years: int, job_text: str) -> Tuple[float, str]:
    """
    Match candidate experience level with job requirements.
    Returns (score_boost, experience_level_description)
    """
    job_text_lower = job_text.lower()
    
    # Detect required experience level from job description
    required_level = "mid"  # default
    required_years = 0
    
    for level, keywords in EXPERIENCE_LEVELS.items():
        if any(keyword in job_text_lower for keyword in keywords):
            required_level = level
    
    # Extract required years from job description
    years_matches = re.findall(r'(\d+)\+?\s*(?:years?|yrs?)', job_text_lower)
    if years_matches:
        required_years = int(years_matches[0])
    
    # Determine candidate level
    if profile_years >= 7:
        candidate_level = "senior"
    elif profile_years >= 3:
        candidate_level = "mid"
    else:
        candidate_level = "junior"
    
    # Calculate match score
    score_boost = 0.0
    description = f"Experience Level: {candidate_level} ({profile_years} years)"
    
    if candidate_level == required_level:
        score_boost = 15.0
        description += " - Perfect experience level match!"
    elif candidate_level == "senior" and required_level in ["mid", "junior"]:
        score_boost = 10.0
        description += " - Overqualified, good sign!"
    elif candidate_level == "mid" and required_level == "junior":
        score_boost = 8.0
        description += " - More experienced than required"
    elif candidate_level == "junior" and required_level in ["mid", "senior"]:
        score_boost = -10.0
        description += " - Under-qualified for this position"
    else:
        score_boost = 5.0
    
    # Adjust if years mismatch
    if required_years > 0 and profile_years < required_years:
        score_boost = max(score_boost - 5, -15)
    
    return score_boost, description


def calculate_education_match(profile_education: str, job_education: str) -> Tuple[float, str]:
    """
    Match candidate education with job requirements.
    Returns (score_boost, education_description)
    """
    profile_level = extract_education_level(profile_education)
    job_level = extract_education_level(job_education)
    
    education_hierarchy = {"phd": 4, "masters": 3, "bachelors": 2, "diploma": 1, "unknown": 0}
    profile_rank = education_hierarchy.get(profile_level, 0)
    job_rank = education_hierarchy.get(job_level, 0)
    
    score_boost = 0.0
    description = f"Education: {profile_level}"
    
    if job_rank == 0:  # No specific education requirement mentioned
        score_boost = 5.0
        description += " - No specific education requirement"
    elif profile_rank >= job_rank:
        score_boost = 8.0
        description += f" - Meets or exceeds required {job_level}"
    elif profile_rank == job_rank - 1:
        score_boost = 3.0
        description += f" - One level below required {job_level}"
    else:
        score_boost = -5.0
        description += f" - Below required education level ({job_level})"
    
    return score_boost, description


def extract_soft_skills(text: str) -> List[str]:
    """Extract soft skills from text."""
    text_lower = text.lower()
    found_soft_skills = []
    
    soft_skill_keywords = SKILL_CATEGORIES.get("soft_skills", [])
    for skill in soft_skill_keywords:
        if skill in text_lower:
            found_soft_skills.append(skill)
    
    return found_soft_skills


def _generate_advanced_suggestions(score, matched_skills, unmatched_skills, job_skills,
                                  profile, job_description, experience_years) -> List[str]:
    """
    Generate advanced, actionable suggestions with project recommendations and detailed gap analysis.
    """
    suggestions = []
    
    try:
        # PROJECT RECOMMENDATION DATABASE
        project_templates = {
            "python": {
                "beginner": "Build a Python CLI task manager with file-based storage (argparse, json)",
                "intermediate": "Create a Python web scraper with data analysis dashboard (BeautifulSoup, pandas, matplotlib)",
                "advanced": "Develop a real-time data pipeline with FastAPI and PostgreSQL (FastAPI, SQLAlchemy, async)"
            },
            "javascript": {
                "beginner": "Build a vanilla JavaScript to-do app with localStorage (HTML5, CSS3, Vanilla JS)",
                "intermediate": "Create a weather app with real API integration (Fetch API, DOM manipulation)",
                "advanced": "Develop a collaborative note-taking app with WebSockets (Node.js, Socket.io, MongoDB)"
            },
            "react": {
                "beginner": "Build a React component library with hooks (React Hooks, Storybook)",
                "intermediate": "Create a full-stack app with React frontend and Node backend (React, Express, MongoDB)",
                "advanced": "Develop a real-time collaboration platform (React, Redux, WebSockets, PostgreSQL)"
            },
            "django": {
                "beginner": "Create a Django blog with user authentication (Django ORM, Django Forms, SQLite)",
                "intermediate": "Build a REST API with Django REST Framework (DRF, JWT, PostgreSQL)",
                "advanced": "Develop a multi-tenant SaaS application (Django, Celery, Redis, Stripe integration)"
            },
            "sql": {
                "beginner": "Design and implement a relational database for e-commerce (Normalization, SQL queries)",
                "intermediate": "Create complex SQL queries with optimization and indexing (Query optimization, CTEs, Window functions)",
                "advanced": "Build a data warehouse with dimensional modeling (Star schema, ETL, Analytics)"
            },
            "devops": {
                "beginner": "Set up CI/CD pipeline with GitHub Actions (GitHub Actions, Docker basics)",
                "intermediate": "Deploy microservices to Kubernetes cluster (Docker, Kubernetes, Helm)",
                "advanced": "Architect infrastructure-as-code with Terraform on AWS (Terraform, AWS, Monitoring)"
            },
            "cloud": {
                "beginner": "Deploy a simple web app to cloud (AWS EC2 or Google Cloud App Engine)",
                "intermediate": "Build serverless functions with cloud services (AWS Lambda, Google Cloud Functions)",
                "advanced": "Design multi-region cloud architecture with auto-scaling and disaster recovery"
            },
            "kubernetes": {
                "beginner": "Deploy a containerized application to Kubernetes locally (Docker, Minikube, kubectl)",
                "intermediate": "Set up a multi-container microservices cluster with Helm charts (Helm, StatefulSets, ConfigMaps)",
                "advanced": "Design a production-grade Kubernetes infrastructure with auto-scaling and monitoring (EKS/AKS, Prometheus, Grafana)"
            },
            "docker": {
                "beginner": "Create Docker images for a simple web application (Dockerfile, Docker Hub)",
                "intermediate": "Build a multi-container application with Docker Compose (Docker Compose, networking, volumes)",
                "advanced": "Optimize Docker images and implement container security best practices (image optimization, registry, security scanning)"
            },
            "terraform": {
                "beginner": "Write Terraform configuration to provision basic cloud resources (EC2, S3, networking)",
                "intermediate": "Build infrastructure modules for reusable Terraform configurations (modules, variables, outputs)",
                "advanced": "Design enterprise-grade Infrastructure-as-Code with remote state and team collaboration (Terraform Cloud, workspaces, CI/CD)"
            },
            "jenkins": {
                "beginner": "Create a simple Jenkins pipeline for basic CI (Jenkinsfile, GitHub webhook integration)",
                "intermediate": "Build a multi-stage CI/CD pipeline with testing and deployment stages (declarative pipeline, artifacts, notifications)",
                "advanced": "Design a scalable Jenkins infrastructure with distributed agents and advanced security (RBAC, Blue Ocean, parallel execution)"
            },
            "ci/cd": {
                "beginner": "Set up automated testing and deployment pipeline (GitHub Actions, GitLab CI, or Jenkins)",
                "intermediate": "Build a complete CI/CD workflow with multiple stages: test, build, deploy (artifact management, rollback strategy)",
                "advanced": "Design enterprise CI/CD infrastructure with canary deployments and zero-downtime releases (blue-green, feature flags)"
            },
            "aws": {
                "beginner": "Deploy a web application to AWS EC2 with RDS database (EC2, RDS, Security Groups)",
                "intermediate": "Build serverless application with Lambda, API Gateway, and DynamoDB (Lambda, API Gateway, S3 events)",
                "advanced": "Design highly available multi-region architecture with CloudFormation and auto-scaling (CloudFormation, ELB, CloudFront)"
            },
            "azure": {
                "beginner": "Deploy a web app to Azure App Service with Azure SQL Database (App Service, SQL Database)",
                "intermediate": "Build containerized application using Azure Container Instances and Azure Container Registry (ACI, ACR, CosmosDB)",
                "advanced": "Design enterprise solutions with Azure Kubernetes Service and Azure DevOps (AKS, Azure DevOps, Traffic Manager)"
            },
            "gcp": {
                "beginner": "Deploy application to Google Cloud App Engine or Compute Engine (App Engine, Compute Engine)",
                "intermediate": "Build serverless application with Cloud Functions and Cloud Datastore (Cloud Functions, Firestore, Pub/Sub)",
                "advanced": "Design scalable architecture with Google Kubernetes Engine and Cloud SQL (GKE, Cloud SQL, BigQuery)"
            },
            "java": {
                "beginner": "Build a Java console application with object-oriented principles (Collections, String API, File I/O)",
                "intermediate": "Create a Spring Boot REST API with database integration (Spring Boot, JPA, PostgreSQL)",
                "advanced": "Develop enterprise application with Spring Cloud microservices (Spring Cloud, Eureka, Config Server)"
            },
            "spring": {
                "beginner": "Create a Spring Boot application with basic CRUD operations (Spring Boot, Spring Data JPA)",
                "intermediate": "Build a REST API with Spring Security and JWT authentication (Spring Security, JWT, H2 Database)",
                "advanced": "Design microservices architecture with Spring Cloud (Service discovery, load balancing, distributed tracing)"
            },
            "nodejs": {
                "beginner": "Build a simple Node.js server with Express routing (Express, body-parser, basic middleware)",
                "intermediate": "Create a full-featured API with MongoDB and authentication (Express, MongoDB, bcrypt, sessions)",
                "advanced": "Design scalable application with clustering and caching (Node clustering, Redis, load balancing)"
            },
            "express": {
                "beginner": "Build a basic Express server with routing and templating (EJS, basic routes, static files)",
                "intermediate": "Create a full REST API with database and user authentication (Mongoose, JWT, error handling)",
                "advanced": "Design production-ready application with middleware, validation, and monitoring (helmet, joi, winston logging)"
            },
            "vue": {
                "beginner": "Build a Vue.js component-based single page application (Vue components, props, events)",
                "intermediate": "Create a full-featured Vue app with Vuex state management (Vuex, routing, API integration)",
                "advanced": "Develop enterprise Vue application with testing and performance optimization (Jest, Nuxt, PWA)"
            },
            "angular": {
                "beginner": "Build an Angular application with components and services (Components, Services, Dependency Injection)",
                "intermediate": "Create a feature-rich app with reactive forms and HTTP client (Reactive Forms, RxJS, HttpClient)",
                "advanced": "Design scalable Angular application with lazy loading and state management (NgRx, lazy loading, performance tuning)"
            },
            "typescript": {
                "beginner": "Convert JavaScript project to TypeScript with basic type annotations (interfaces, types, strict mode)",
                "intermediate": "Build a typed Node.js/React project with advanced TypeScript features (generics, decorators, advanced types)",
                "advanced": "Design type-safe architecture with complex generics and utility types (conditional types, mapped types, modules)"
            },
            "mongodb": {
                "beginner": "Design and implement a simple MongoDB database for a web application (collections, documents, basic queries)",
                "intermediate": "Build a structured MongoDB schema with relationships and indexing (aggregation, indexes, validation)",
                "advanced": "Design a scalable MongoDB infrastructure with replication and sharding (replica sets, sharding, transactions)"
            },
            "postgresql": {
                "beginner": "Design a relational database schema and write basic SQL queries (tables, relationships, SELECT/INSERT/UPDATE)",
                "intermediate": "Create complex queries with joins, subqueries, and stored procedures (advanced queries, functions, triggers)",
                "advanced": "Optimize PostgreSQL performance with indexing and tuning (query optimization, EXPLAIN ANALYZE, partitioning)"
            },
            "mysql": {
                "beginner": "Set up MySQL database and create tables with relationships (CREATE TABLE, PRIMARY KEY, FOREIGN KEY)",
                "intermediate": "Write optimized SQL queries and stored procedures (JOINs, indexing, prepared statements, functions)",
                "advanced": "Design high-performance MySQL infrastructure with replication (replication, backup, sharding strategies)"
            },
            "redis": {
                "beginner": "Use Redis for caching in a simple web application (SET/GET, expiration, basic operations)",
                "intermediate": "Implement Redis for session storage and pub/sub messaging (Hashes, Lists, pub/sub, pipelines)",
                "advanced": "Design Redis cluster infrastructure for high availability (cluster mode, sentinel, Lua scripting)"
            },
            "microservices": {
                "beginner": "Break down a monolith into 2-3 basic microservices (service separation, basic communication)",
                "intermediate": "Build microservices with API Gateway and service discovery (API Gateway, load balancing, communication patterns)",
                "advanced": "Design distributed microservices with circuit breakers and event streaming (Kafka, circuit breakers, sagas)"
            },
            "rest": {
                "beginner": "Design and build a basic REST API following conventions (GET, POST, PUT, DELETE, status codes)",
                "intermediate": "Implement a secure REST API with authentication, versioning, and documentation (JWT, API versioning, Swagger/OpenAPI)",
                "advanced": "Design scalable REST API with caching, pagination, and advanced filtering (ETags, pagination, rate limiting)"
            },
            "graphql": {
                "beginner": "Build a basic GraphQL server with queries and mutations (Apollo Server, schema definition, resolvers)",
                "intermediate": "Create a GraphQL API with authentication and complex schema relationships (authentication, subscriptions, nested queries)",
                "advanced": "Design production GraphQL infrastructure with federation and performance optimization (Apollo Federation, caching, batch loading)"
            },
            "go": {
                "beginner": "Build a simple Go application with basic concurrency (goroutines, channels, packages)",
                "intermediate": "Create a Go web service with REST API and database (Gin framework, GORM, middleware)",
                "advanced": "Design high-performance Go application with advanced concurrency patterns (channels, select, worker pools)"
            },
            "rust": {
                "beginner": "Build a Rust CLI application with file operations (ownership, borrowing, basic stdlib)",
                "intermediate": "Create a Rust web service with actix-web framework (actix, async/await, error handling)",
                "advanced": "Design system-level Rust application with memory safety and performance (unsafe code, FFI, optimization)"
            },
            "docker": {
                "beginner": "Create Dockerfile for containerizing a simple application (Dockerfile, image layers, basic commands)",
                "intermediate": "Build multi-stage Docker images and Docker Compose setup (multi-stage builds, Compose, networking)",
                "advanced": "Optimize Docker images for production and implement container security (image optimization, scanning, signing)"
            },
            "git": {
                "beginner": "Learn Git fundamentals and basic workflow (init, add, commit, push, pull, branches)",
                "intermediate": "Master branching strategies and collaboration (feature branches, merge conflicts, pull requests)",
                "advanced": "Implement advanced Git workflows and automation (rebase, cherry-pick, hooks, scripting)"
            },
            "linux": {
                "beginner": "Learn Linux basics and command-line operations (file system, permissions, basic commands)",
                "intermediate": "Master Linux system administration tasks (users, packages, networking, services)",
                "advanced": "Design and optimize Linux infrastructure (kernel tuning, security hardening, performance monitoring)"
            },
            "default": {
                "beginner": "Build a GitHub portfolio project showcasing this technology stack",
                "intermediate": "Create an end-to-end project combining frontend, backend, and database",
                "advanced": "Contribute to open-source projects in this technology area"
            }
        }
        
        # RESUME GAP ANALYSIS
        gap_analysis = _analyze_resume_gaps(profile, job_description, unmatched_skills, experience_years)
        
        # SCORE-BASED ADVANCED SUGGESTIONS
        if score < 40:
            suggestions.append(f"\n🎯 MATCH ASSESSMENT: Low match ({score}%) - Significant gaps detected\n")
            
            suggestions.append("📋 RESUME GAPS IDENTIFIED:")
            for gap in gap_analysis:
                suggestions.append(f"   • {gap}")
            
            if unmatched_skills:
                suggestions.append(f"\n🔧 PRIORITY SKILLS TO DEVELOP ({len(unmatched_skills)} gaps):")
                for skill in unmatched_skills[:5]:
                    skill_lower = skill.lower()
                    skill_type = _classify_skill_level(matched_skills, experience_years)
                    projects = project_templates.get(skill_lower, project_templates["default"])
                    project = projects.get(skill_type, projects.get("intermediate"))
                    suggestions.append(f"   • {skill.title()}: {project}")
            
            suggestions.append(f"\n📈 RECOMMENDED ACTION PLAN (3-6 months):")
            suggestions.append(f"   1. Pick 2-3 priority skills from above")
            suggestions.append(f"   2. Build 1-2 portfolio projects demonstrating these skills")
            suggestions.append(f"   3. Update resume with new projects and achievements")
            suggestions.append(f"   4. Consider this role after developing core skills")
            
        elif score < 60:
            suggestions.append(f"\n⚠️  MATCH ASSESSMENT: Below-average match ({score}%) - Tailor your application\n")
            
            suggestions.append("📋 RESUME GAPS TO ADDRESS:")
            for gap in gap_analysis:
                suggestions.append(f"   • {gap}")
            
            if unmatched_skills:
                suggestions.append(f"\n🎓 KEY MISSING SKILLS ({len(unmatched_skills)} gaps):")
                for skill in unmatched_skills[:3]:
                    skill_lower = skill.lower()
                    projects = project_templates.get(skill_lower, project_templates["default"])
                    project = projects.get("intermediate", projects.get("beginner"))
                    suggestions.append(f"   • {skill.title()}: {project}")
            
            suggestions.append(f"\n💼 APPLICATION STRATEGY:")
            suggestions.append(f"   1. Write a cover letter explaining relevant experience transfer")
            suggestions.append(f"   2. Highlight any adjacent skills or related projects")
            suggestions.append(f"   3. Show willingness to learn missing skills on the job")
            suggestions.append(f"   4. Suggest yourself as 'high potential' for growth")
            
        elif score < 75:
            suggestions.append(f"\n✅ MATCH ASSESSMENT: Good match ({score}%) - Strong candidate\n")
            
            if gap_analysis:
                suggestions.append("🚀 AREAS FOR IMPROVEMENT:")
                for gap in gap_analysis[:2]:
                    suggestions.append(f"   • {gap}")
            
            if unmatched_skills:
                suggestions.append(f"\n💡 NICE-TO-HAVE SKILLS ({len(unmatched_skills)} bonus skills):")
                for skill in unmatched_skills[:2]:
                    skill_lower = skill.lower()
                    projects = project_templates.get(skill_lower, project_templates["default"])
                    project = projects.get("intermediate")
                    suggestions.append(f"   • {skill.title()}: {project}")
            
            suggestions.append(f"\n📊 APPLICATION TIPS:")
            suggestions.append(f"   1. Lead with your {len(matched_skills)} strong matched skills")
            suggestions.append(f"   2. Show concrete achievements in matched technologies")
            suggestions.append(f"   3. Mention interest in learning {unmatched_skills[0] if unmatched_skills else 'new skills'}")
            suggestions.append(f"   4. Apply with confidence - you're well-positioned")
            
        else:
            suggestions.append(f"\n🌟 MATCH ASSESSMENT: Excellent match ({score}%) - Ideal candidate!\n")
            suggestions.append(f"✨ You meet {len(matched_skills)}/{len(job_skills)} required skills")
            suggestions.append(f"\n💪 YOUR STRENGTHS:")
            strengths = matched_skills[:5]
            for skill in strengths:
                suggestions.append(f"   • {skill.title()} (verified match)")
            
            suggestions.append(f"\n🎯 NEXT STEPS:")
            suggestions.append(f"   1. Customize your resume highlighting these {len(matched_skills)} matched skills")
            suggestions.append(f"   2. Prepare examples of projects using these technologies")
            suggestions.append(f"   3. Apply immediately - this is a strong fit")
            suggestions.append(f"   4. In interview, emphasize your relevant project experience")
        
        return suggestions
    
    except Exception as e:
        import traceback
        print(f"Error in _generate_advanced_suggestions: {str(e)}")
        traceback.print_exc()
        return [f"Match score: {score}% - Suggestion generation temporarily unavailable. Please try again."]


def _analyze_resume_gaps(profile, job_description, unmatched_skills, experience_years) -> List[str]:
    """
    Analyze specific gaps in resume compared to job requirements.
    """
    gaps = []
    job_lower = job_description.lower()
    
    try:
        # Check summary quality
        summery = getattr(profile, 'summery', 'Not Provided') or 'Not Provided'
        if not summery or summery == "Not Provided" or len(str(summery).split()) < 20:
            gaps.append("Professional summary is missing or too brief - Add 30-50 word professional summary")
        
        # Check experience gaps
        if experience_years < 2:
            gaps.append(f"Limited professional experience ({experience_years} years) - Build projects to compensate")
        
        # Check education gaps
        education = getattr(profile, 'education', 'Not Provided') or 'Not Provided'
        if not education or education == "Not Provided":
            gaps.append("Education details not provided - Add degree, institution, graduation year")
        
        # Check portfolio/projects
        projects = getattr(profile, 'projects', '') or ''
        if not projects or projects == "Not Provided" or projects.strip() == "":
            gaps.append("No projects listed - Add 2-3 relevant GitHub projects with descriptions")
        
        # Check certifications for advanced roles
        if "senior" in job_lower or "lead" in job_lower:
            certifications = getattr(profile, 'certifications', '') or ''
            if not certifications or len(str(certifications).split(",")) < 2:
                gaps.append("Few certifications/credentials - Add relevant industry certifications")
        
        # Check for required tech stack completeness
        if "fullstack" in job_lower or "full stack" in job_lower:
            skills = getattr(profile, 'skills', '') or ''
            skills_str = skills.lower() if skills and skills != "Not Provided" else ""
            has_frontend = any(fw in skills_str for fw in ["react", "vue", "angular", "frontend", "html", "css"])
            has_backend = any(bw in skills_str for bw in ["django", "nodejs", "node.js", "spring", "backend", "python", "java"])
            if not has_frontend or not has_backend:
                gaps.append("Full-stack role requires both frontend and backend skills - Develop both areas")
        
        return gaps if gaps else ["Resume is well-aligned with job requirements"]
    except Exception as e:
        print(f"Error in _analyze_resume_gaps: {str(e)}")
        return ["Resume analysis unavailable - please ensure profile is complete"]


def _classify_skill_level(matched_skills, experience_years) -> str:
    """Classify whether candidate should build beginner, intermediate, or advanced projects."""
    if experience_years >= 5 or len(matched_skills) >= 8:
        return "advanced"
    elif experience_years >= 2 or len(matched_skills) >= 4:
        return "intermediate"
    return "beginner"


def calculate_match_score(profile, job_description):
    """
    Enhanced job matching algorithm with multiple scoring factors.
    Returns (score, reasons, missing_skills, suggestions)
    """
    reasons = []
    suggestions = []
    score_components = {}
    
    # Calculate experience years from experience field
    experience_years = 0
    experience = getattr(profile, 'expirence', 'Not Provided') or 'Not Provided'
    if experience and experience != "Not Provided":
        try:
            # Try to extract years as a number from the experience text
            import re as re_module
            years_match = re_module.search(r'(\d+)', str(experience))
            if years_match:
                experience_years = int(years_match.group(1))
            else:
                # Default to 2 if experience mentioned but no number found
                experience_years = 2 if experience.strip() else 0
        except:
            experience_years = 0
    
    jd_lower = job_description.lower()
    jd_skills = extract_skills_from_text(jd_lower)
    
    # ===== SKILL MATCHING =====
    profile_skills = []
    skill_proficiency = {"beginner": 0, "intermediate": 0, "advanced": 0}
    
    if profile.skills and profile.skills != "Not Provided":
        # First, detect proficiency levels from the raw text
        skills_lower = profile.skills.lower()
        if any(term in skills_lower for term in ["advanced", "expert", "senior"]):
            skill_proficiency["advanced"] += 1
        elif any(term in skills_lower for term in ["intermediate", "experienced"]):
            skill_proficiency["intermediate"] += 1
        elif any(term in skills_lower for term in ["beginner", "basic", "familiar"]):
            skill_proficiency["beginner"] += 1
        
        # Use extract_skills_from_text() to properly extract skills
        # This ensures consistent skill normalization and matching
        profile_skills = extract_skills_from_text(profile.skills)
    
    # Remove duplicates (already done by extract_skills_from_text but ensure it)
    profile_skills = list(dict.fromkeys(profile_skills))
    
    # Calculate skill match
    skill_percentage, matched_skills, unmatched_skills = calculate_skill_match_score(
        profile_skills, jd_skills, skill_proficiency
    )
    score_components["skills"] = skill_percentage
    
    if matched_skills:
        reasons.append(f"📊 Skill Match Rate: {len(matched_skills)}/{len(jd_skills)} ({skill_percentage:.0f}%)")
        reasons.append(f"✅ Matched Skills: {', '.join(matched_skills[:8])}")
        
        if skill_proficiency["advanced"] > 0:
            reasons.append(f"🔥 Advanced proficiency in {skill_proficiency['advanced']} skill(s)")
        
        # Categorize matched skills
        matched_categories = categorize_skills(matched_skills)
        if matched_categories:
            category_list = ", ".join(matched_categories.keys())
            reasons.append(f"🎯 Coverage: {category_list}")
    else:
        reasons.append("⚠️ No matching skills detected - significant skill gap")
        suggestions.append("🔍 Carefully review the job requirements and identify priority skills")
    
    # ===== EXPERIENCE MATCHING =====
    profile_years = 0
    if profile.expirence and profile.expirence != "Not Provided":
        profile_years = extract_experience_years(profile.expirence)
    
    exp_score_boost, exp_description = calculate_experience_match(profile_years, jd_lower)
    score_components["experience"] = exp_score_boost
    reasons.append(f"⏱️ {exp_description}")
    
    # ===== EDUCATION MATCHING =====
    profile_education = profile.education if hasattr(profile, 'education') and profile.education else ""
    edu_score_boost, edu_description = calculate_education_match(profile_education, jd_lower)
    score_components["education"] = edu_score_boost
    reasons.append(f"🎓 {edu_description}")
    
    # ===== SOFT SKILLS MATCHING =====
    job_soft_skills = extract_soft_skills(jd_lower)
    profile_soft_skills = extract_soft_skills(profile.summery if profile.summery else "")
    profile_soft_skills.extend(extract_soft_skills(profile.expirence if profile.expirence else ""))
    
    soft_skill_matches = [s for s in job_soft_skills if s in profile_soft_skills]
    soft_skill_boost = 0.0
    if job_soft_skills:
        soft_skill_ratio = len(soft_skill_matches) / len(job_soft_skills)
        soft_skill_boost = soft_skill_ratio * 10
        if soft_skill_matches:
            reasons.append(f"💬 Soft Skills: {', '.join(soft_skill_matches)}")
    
    score_components["soft_skills"] = soft_skill_boost
    
    # ===== SUMMARY ALIGNMENT =====
    summary_boost = 0.0
    if profile.summery and profile.summery != "Not Provided":
        summary_lower = profile.summery.lower()
        summary_words = set(summary_lower.split())
        jd_words = set(jd_lower.split())
        
        # Filter out common words
        common_words = {"the", "a", "an", "and", "or", "is", "are", "in", "on", "at", "to", "for"}
        overlap = len(summary_words - common_words) & len(jd_words - common_words)
        
        if len(summary_words) > 30:
            if overlap > 10:
                summary_boost = 8.0
                reasons.append(f"📝 Strong summary alignment with job keywords")
            elif overlap > 5:
                summary_boost = 4.0
                reasons.append(f"📋 Moderate summary alignment")
            else:
                suggestions.append("🔍 Improve your summary to align better with job terminology")
        else:
            suggestions.append("📏 Expand your summary - currently too brief")
    else:
        suggestions.append("📋 Add a professional summary highlighting relevant experience")
    
    score_components["summary"] = summary_boost
    
    # ===== CALCULATE FINAL SCORE =====
    # Weighted average of components
    weights = {
        "skills": 0.50,
        "experience": 0.20,
        "education": 0.10,
        "soft_skills": 0.10,
        "summary": 0.10
    }
    
    final_score = sum(score_components.get(key, 0) * weight 
                      for key, weight in weights.items())
    
    # Cap score at 99 and minimum 0
    final_score = max(0, min(final_score, 99))
    
    # ===== GENERATE ADVANCED SUGGESTIONS WITH PROJECT RECOMMENDATIONS =====
    advanced_suggestions = _generate_advanced_suggestions(
        final_score, matched_skills, unmatched_skills, jd_skills,
        profile, job_description, experience_years
    )
    suggestions.extend(advanced_suggestions)
    
    return int(final_score), reasons, unmatched_skills, suggestions